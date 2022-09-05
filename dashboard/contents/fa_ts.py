from ggdb.models import Corp, FsAccount, FsDetail

import json
import pandas as pd

class FaTs:
    def __init__(self, acnt_nm, oc, stock_code):
        self.oc = oc
        corp = Corp.objects.get(stockCode=stock_code)
        fltr = {
            'account__accountNm': acnt_nm,
            'fs__corp': corp,
            'fs__type__oc': oc,
        }

        FIELDS = {
            'fs__fqe': 'fqe',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'fs__type__name': 'ft',
            'value': 'value'
        }
        qs = FsDetail.objects.filter(**fltr)
        if not qs.exists():
            raise KeyError('no data')

        df = pd.DataFrame.from_records(qs.values(*FIELDS.keys())).rename(columns=FIELDS)

        ft_prefix_uniq = df.ft.str[:-1].unique()
        if ('IS' in ft_prefix_uniq) and ('CIS' in ft_prefix_uniq):
            df = df.loc[df.ft.str[:-1] != 'CIS']

        ft_count = df.ft.value_counts().to_dict()
        df['ft_order'] = df.ft.replace(ft_count)
        df = df.sort_values(
            ['fqe', 'ft_order'],
            ascending = [False, False]
        ).drop_duplicates('fqe')
        del df['ft_order']

        df.fqe = pd.to_datetime(df.fqe)

        df = df.sort_values('fqe')
        mgap = df.fqe.dt.month - corp.fye
        ydiff =  -((mgap <= 0) & (corp.fye != 12)).astype(int)
        df.by = df.fqe.dt.year + ydiff
        df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

        self.fa = FsAccount.objects.filter(
            accountNm = acnt_nm,
            type__oc = oc,
        ).first()
        is_not_flow = self.fa.type.type == 'BS'
        if is_not_flow:
            self.ts = df[['fqe','value']]
        else:
            idx2fqe = (
                df[['by','bq','fqe']]
                .set_index(['by','bq'])
                .fqe.to_dict()
            )
            dfq = (
                df[['by','bq','value']]
                .set_index(['by','bq'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1]+dfq[2]+dfq[3])
            dfq = dfq.stack().rename('value').to_frame()
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            self.ts = dfq.reset_index()[['fqe','value']]

        self._fa_info = None
        self._graph_data = None

    def update_fa_info(self):
        self._fa_info = {
            'oc': self.oc,
            'nm': self.fa.accountNm,
            'lk': self.fa.labelKor,
            'path': ' / '.join([
                fa.labelKor.replace('[abstract]','').strip()
                for fa in get_fa_path(self.fa, [])
            ])
        }

    def update_graph_data(self):
        ts = self.ts.copy()
        ts['growth'] = (ts.value / ts.value.shift(1) - 1) * 100
        is_big_gap = ts.fqe - ts.fqe.shift(1) > '95 days'
        ts.growth[is_big_gap] = None
        self._graph_data = {
            'x': ts.fqe.to_json(orient='records'),
            'y_value': ts.value.to_json(orient='records'),
            'y_growth': ts.growth.to_json(orient='records')
        }

    def get_data(self):
        return json.dumps({
            'fa_info': self._fa_info,
            'graph_data': self._graph_data,
        })


        # self.ts = self.ars.get_time_series(self.corp.stockCode)
        # self._dateformatter = lambda tp: f"{tp.year}-{str(tp.month).zfill(2)}-{str(tp.day).zfill(2)}"
        # self._hex_to_rgba = lambda h, opacity: (
        #     f"rgba{tuple([int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)] + [opacity])}"
        # )
        # self._graph_data = None
        # self._layout = None
        # self._global_props = None
        # self._traces = None
        # self._frames = None
        # self._sliders = None

def get_fa_path(fa, container):
    if fa.parent:
        new_container = [fa.parent] + container
        return get_fa_path(fa.parent, new_container)
    else:
        return container
