from ggdb.models import *
from itertools import islice

import json

class AccountRatioManager:

    def __init__(self):
        self.ar_all = AccountRatio.objects.all()
        with open('source/account_ratios.json') as f:
            self.data = json.load(f)

    def update(self):
        print('updating account_ratio...')
        ar_created = []
        for d in self.data:
            if not AccountRatio.objects.filter(name=d['name']).exists():
                ar_created.append(AccountRatio(**d))
        if len(ar_created) > 0:
            AccountRatio.objects.bulk_create(ar_created)
            print('...following account ratios are newly defined.')
            for ar in ar_created:
                print(f"......{ar.name}")
        else:
            print('...no new account ratio')

    def update_values(self):
        print('updating account_ratio_value...')
        arv_created, arv_updated, arvh_all = [], [], []
        for ar in self.ar_all:
            print(f'...calculating values of {ar.name}')
            arv_all = ar.values.all().select_related('ar','corp')
            comb2arv = {(arv.ar.id, arv.corp.id, arv.fqe, arv.oc): arv for arv in arv_all}
            for oc, mkt in OC_MKT_ORD:
                try:
                    panel = ar.get_panel(oc, mkt)
                except ValueError:
                    continue

                new_arv_all = panel.reset_index().to_dict(orient='records')
                for new_arv in new_arv_all:
                    arv = comb2arv.pop(
                        (
                            ar.id,
                            new_arv['corp_id'],
                            new_arv['fqe'],
                            oc,
                        ), None
                    )
                    if arv == None:
                        arv_created.append(AccountRatioValue(**{
                            'ar_id': ar.id,
                            **new_arv,
                            'oc': oc,
                        }))
                    else:
                        if arv.value != new_arv['value']:
                            arvh_all.append(AccountRatioValueHistory(
                                arv = arv,
                                prevValue = arv.value
                            ))
                            arv.value = new_arv['value']
                            arv_updated.append(arv)

        batch_size = 100000
        if len(arv_created) > 0:
            while True:
                print(f"...{len(arv_created)} rows were left to be created.")
                batch_c = list(islice(arv_created, batch_size))
                if not batch_c:
                    break
                AccountRatioValue.objects.bulk_create(batch_c, batch_size)
                arv_created = arv_created[batch_size:]
        else:
            print('...no new account ratio value.')

        if len(arv_updated) > 0:
            while True:
                print(f"...{len(arv_updated)} rows were left to be updated.")
                batch_u = list(islice(arv_updated, batch_size))
                if not batch_u:
                    break
                AccountRatioValue.objects.bulk_update(batch_u, ['value'], batch_size)
                arv_updated = arv_updated[batch_size:]
        else:
            print('...no change in account ratio value.')

        if len(arvh_all) > 0:
            while True:
                print(f"...{len(arvh_all)} new history were left to be created.")
                batch_h = list(islice(arvh_all, batch_size))
                if not batch_h:
                    break
                AccountRatioValueHistory.objects.bulk_create(batch_h, batch_size)
                arvh_all = arvh_all[batch_size:]

        print("...complete!")

    def update_latest_values(self):
        print("updating 'isLatest' in account_ratio_value...")
        oc_mkt_ord = [
            ('CFS', 'KOSPI'),
            ('OFS', 'KOSPI'),
            ('CFS', 'KOSDAQ'),
            ('OFS', 'KOSDAQ'),
        ]
        arv_updated = []
        for ar in self.ar_all:
            for oc, mkt in oc_mkt_ord:
                print(f"...collecting the updates in the latest values of {ar.name} for {oc}_{mkt}.")
                latest_all = ar.values.filter(method=oc, corp__market=mkt, isLatest=True)
                try:
                    new_latest_all = ar.inspect_latest_all(oc, mkt)
                except ValueError:
                    continue

                # latest to old
                be_old_all = [arv for arv in latest_all if arv not in new_latest_all]
                for arv in be_old_all:
                    arv.isLatest = False
                    arv_updated.append(arv)

                # new latest
                be_latest_all = [arv for arv in new_latest_all if arv not in latest_all]
                for arv in be_latest_all:
                    arv.isLatest = True
                    arv_updated.append(arv)

        batch_size = 100000
        if len(arv_updated) > 0:
            while True:
                print(f"...{len(arv_updated)} rows were left to be updated.")
                batch_u = list(islice(arv_updated, batch_size))
                if not batch_u:
                    break
                AccountRatioValue.objects.bulk_update(batch_u, ['isLatest'], batch_size)
                arv_updated = arv_updated[batch_size:]
        else:
            print("...no change in 'isLatest' of account_ratio_value.")

        print("...complete!")


def get_dominant_series_by_oc(dfa, oc):
    if oc == 'OFS':
        fltr_oc = dfa.fstype.str[-1:].astype(int) % 2 == 0
    elif oc == 'CFS':
        fltr_oc = dfa.fstype.str[-1:].astype(int) % 2 == 1
    dfa_oc = dfa.loc[fltr_oc].copy()
    ft_count = dfa_oc.fstype.value_counts()
    ft_order_map = {k: i for i, k in enumerate(ft_count.keys())}
    dfa_oc['ft_order'] = dfa_oc.fstype.replace()
    del dfa_oc['fstype']
    idcols = ['corp_id', 'by', 'bq']
    dfa_oc = dfa_oc.sort_values(idcols+['ft_order'], ascending=[True,False,False,True]).drop_duplicates(idcols)
    del dfa_oc['ft_order']
    return dfa_oc.set_index(idcols)['value']#.rename(oc)



class LatestAccountRatio:

    def __init__(self, ar, **kwargs):
        self.ar = ar

        fltr = {
            'isLatest': True,
            'corp__delistedAt__isnull': True,
        }
        include_delisted = kwargs.pop('include_delisted', False)
        if include_delisted:
            fltr.pop('corp__delistedAt__isnull', None)
        self.qs = ar.values.filter(**fltr).select_related('corp')

    def get_series(self, oc, mkt):
        fields = {
            'corp__stockCode': 'stock_code',
            'corp__corpName': 'corp_name',
            'by': 'by',
            'bq': 'bq',
            'value': 'value',
        }
        indexes = ['stock_code','corp_name','by','bq']
        qss = (
            self.qs.filter(method=oc, corp__market=mkt)
            .select_related('corp')
        )
        if not qss.exists():
            raise ValueError(f"{oc}_{mkt} has no attribute of {self.ar.name}.")

        return pd.DataFrame.from_records(
            qss.values(*fields.keys())
        ).rename(columns=fields).set_index(indexes).value


class LatestAccountRatioManager:

    def __init__(self):
        self.tempfile_path = lambda oc, mkt: f"ggdb/temp/dashboard/latest_account_ratio_all_{oc}_{mkt}.json"
        self.oc_mkt_ord = [
            ('CFS', 'KOSPI'),
            ('OFS', 'KOSPI'),
            ('CFS', 'KOSDAQ'),
            ('OFS', 'KOSDAQ'),
        ]

    def update_temp(self):
        print('writing temp data for latest_account_ratio')
        ar_all = AccountRatio.objects.all()
        for oc, mkt in self.oc_mkt_ord:
            print(f"...writing '{self.tempfile_path(oc, mkt)}'")
            lar_all = []
            for ar in ar_all:
                try:
                    lar_all.append(
                        LatestAccountRatio(ar)
                        .get_series(oc,mkt)
                        .rename(ar.name)
                    )
                except ValueError:
                    continue

            df = pd.concat(lar_all, axis=1)
            with open(self.tempfile_path(oc, mkt), 'w') as f:
                json.dump(
                    json.loads(
                        df.round(4).reset_index()
                        .sort_values(
                            ['stock_code','by','bq'],
                            ascending=[True,False,False]
                        ).to_json(orient='records')
                    ), f
                )
        print('...complete!')

    def read_temp(self, oc, mkt, **kwargs):
        corp = kwargs.pop('corp', None)
        ar = kwargs.pop('ar', None)
        with open(self.tempfile_path(oc, mkt)) as f:
            data = json.load(f)

        if (corp == None) & (ar == None):
            return data

        elif (corp == None) & (ar != None):
            if ar.name not in data[0].keys():
                raise KeyError(ar.name)
            reduced_data = []
            for d in data:
                reduced_d = {}
                reduced_d['stock_code'] = d.pop('stock_code')
                reduced_d['corp_name'] = d.pop('corp_name')
                reduced_d['by'] = d.pop('by')
                reduced_d['bq'] = d.pop('bq')
                reduced_d['value'] = d.pop(ar.name)
                reduced_data.append(reduced_d)
            return reduced_data

        elif (corp != None) & (ar == None):
            corp_data = list(filter(
                lambda x: x['stock_code'] == corp.stockCode,
                data
            ))
            if len(corp_data) == 0:
                raise ValueError(f"no such corp in {mkt}.")
            return corp_data

        else:
            corp_data = list(filter(
                lambda x: x['stock_code'] == corp.stockCode,
                data
            ))
            if len(corp_data) == 0:
                raise ValueError(f"no such corp in {mkt}.")
            reduced_data = []
            for d in corp_data:
                reduced_d = {}
                reduced_d['stock_code'] = d.pop('stock_code')
                reduced_d['corp_name'] = d.pop('corp_name')
                reduced_d['by'] = d.pop('by')
                reduced_d['bq'] = d.pop('bq')
                reduced_d['value'] = d.pop(ar.name)
                reduced_data.append(reduced_d)
            return reduced_data


class AggregateAccountRatioManager:

    def __init__(self):
        self.tempfile_path = lambda oc, mkt: f"ggdb/temp/dashboard/aggregate_account_ratio_all_{oc}_{mkt}.json"
        self.oc_mkt_ord = [
            ('CFS', 'KOSPI'),
            ('OFS', 'KOSPI'),
            ('CFS', 'KOSDAQ'),
            ('OFS', 'KOSDAQ'),
        ]

    def update_temp(self):
        print('writing temp data for aggregate_account_ratio')
        ar_all = AccountRatio.objects.all()
        for oc, mkt in self.oc_mkt_ord:
            print(f"...writing '{self.tempfile_path(oc, mkt)}'")
            agg_ar_all = []
            for ar in ar_all:
                try:
                    ar_mean = ar.get_aggregate_time_series(oc, mkt, method='mean', bounds=[.025,.975]).rename(f"mean_{ar.name}")
                except ValueError:
                    continue
                ar_median = ar.get_aggregate_time_series(oc, mkt, method='median').rename(f"median_{ar.name}")
                agg_ar_all += [ar_mean, ar_median]


            df = pd.concat(agg_ar_all, axis=1)
            with open(self.tempfile_path(oc, mkt), 'w') as f:
                json.dump(
                    json.loads(
                        df.round(4).reset_index()
                        .sort_values(['by','bq'])
                        .to_json(orient='records')
                    ), f
                )
        print('...complete!')

    def read_temp(self, oc, mkt, **kwargs):
        ar = kwargs.pop('ar', None)
        aggmethod = kwargs.pop('method', None)
        with open(self.tempfile_path(oc, mkt)) as f:
            data = json.load(f)

        if (ar == None) & (aggmethod == None):
            return data

        else:
            if (ar == None) & (aggmethod != None):
                tgkey_all = [
                    k for k in data[0].keys()
                    if (k not in ['by', 'bq'])
                    and (k.split('_')[0] == aggmethod)
                ]

            elif (ar != None) & (aggmethod == None):
                tgkey_all = [
                    k for k in data[0].keys()
                    if (k not in ['by', 'bq'])
                    and (k.split('_')[1] == ar.name)
                ]
                if len(tgkey_all) == 0:
                    raise KeyError(ar.name)

            else:
                tgkey_all = [
                    k for k in data[0].keys()
                    if (k not in ['by', 'bq'])
                    and (k.split('_')[0] == aggmethod)
                    and (k.split('_')[1] == ar.name)
                ]
                if len(tgkey_all) == 0:
                    raise KeyError(ar.name)

            reduced_data = []
            for d in data:
                reduced_d = {}
                reduced_d['by'] = d.pop('by')
                reduced_d['bq'] = d.pop('bq')
                for k in tgkey_all:
                    reduced_d[k] = d.pop(k)
                reduced_data.append(reduced_d)
            return reduced_data
