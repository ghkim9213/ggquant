from .data.ar import ArSeries
from .data.fa import FaSeries
from .data.tools import *
from .tools import *

from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
from dashboard.models import FaCrossSection
from django.db.models import Max
from ggdb.models import Corp, AccountRatio
from ggdb.models import FsAccountLite

import json
import numpy as np
import pandas as pd

class CustomAr:
    def __init__(self, stock_code, channel_name):
        # ar_nm, oc,
        self.channel_layer = get_channel_layer()
        self.channel_name = channel_name

        self.stock_code = stock_code
        self.market = Corp.objects.get(stockCode=stock_code).market

    def check_item(self, oc, acnt_nm):
        fas = FaSeries(acnt_nm, oc)
        ts = fas.time_series(self.stock_code)

        data = json.dumps({
            'item': fas.fa.info,
            'status': {
                'ts': len(ts) > 0,
                'cs': fas.fa.inspect(),
            },
        })

        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'send.car',
                'text': data,
            }
        )

    def check_car(self, custom_ar):
        data = {}

        # return input back
        ar_all = AccountRatio.objects.all()
        serial_num = ar_all.aggregate(Max('id'))['id__max'] + 1

        inputs = custom_ar.copy()
        inputs['create'] = True
        car_nm = custom_ar.pop('nm')
        if car_nm:
            inputs['nm'] = ''.join([
                word.capitalize()
                for word in
                inputs['nm'].replace('  ',' ').split(' ')
            ])
        else:
            DEFAULT_AR_NAME_PREFIX = 'UserDefinedAccountRatio';
            default_nm = f"{DEFAULT_AR_NAME_PREFIX}{str(serial_num).zfill(6)}"
            inputs['nm'] = default_nm

        car_lk = custom_ar.pop('lk')
        if car_lk:
            inputs['lk'] = car_lk.replace(' ', '')
        else:
            DEFAULT_AR_LK_PREFIX = '사용자정의재무비율'
            default_lk = f"{DEFAULT_AR_LK_PREFIX}{str(serial_num).zfill(6)}"
            inputs['lk'] = default_lk

        data['inputs'] = inputs

        # find matched ar
        car_syntax = custom_ar.pop('operation')
        car_items = custom_ar.pop('items')
        for item in car_items:
            car_syntax = car_syntax.replace(
                item['letter'],
                f"[{item['letter']}]"
            )
        for item in car_items:
            car_syntax = car_syntax.replace(
                f"[{item['letter']}]",
                f"{item['nm']}_{item['oc']}"
            )
        created = True
        for ar in ar_all:
            r = ar.to_request()
            if custom_ar['changeIn'] != r['changeIn']:
                continue
            oper_equiv = get_oper_equiv(r['operation'])
            syntax = r['operation']
            for oper in oper_equiv:
                for item in r['items']:
                    syntax = syntax.replace(
                        item['letter'],
                        f"[{item['letter']}]"
                    )
                for item in r['items']:
                    syntax = syntax.replace(
                        f"[{item['letter']}]",
                        f"{item['nm']}_{item['oc']}"
                    )
                if syntax == car_syntax:
                    created = False
                    break
            if created == False:
                break

        if created:
            data['matched'] = None
        else:
            r['create'] = False
            data['matched'] = r

        # non-batched items
        non_batched_items = []
        for item in car_items:
            item_exists = FsAccountLite.objects.get(
                name = item['nm'],
                oc = item['oc']
            ).cs.exists()
            if not item_exists:
                non_batched_items.append(item)
        data['non_batched_items'] = non_batched_items
        data = json.dumps(data)

        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'send.car',
                'text': data,
            }
        )

    def get_ts_data(self, custom_ar):
        if custom_ar['create']:
            item_obj_all = [
                FsAccountLite.objects.get(
                    name = item['nm'],
                    oc = item['oc']
                ) for item in custom_ar['items']
            ]
            syntax = custom_ar['operation']
            for item in custom_ar['items']:
                syntax = syntax.replace(
                    item['letter'],
                    f"[{item['letter']}]"
                )
            for item in custom_ar['items']:
                syntax = syntax.replace(
                    f"[{item['letter']}]",
                    f"`{item['nm']}`",
                )

            car, created = AccountRatio.objects.get_or_create(
                name = custom_ar['nm'],
                abbrev = None if custom_ar['abbrev'] == '' else custom_ar['abbrev'],
                div = custom_ar['carDiv'],
                labelKor = custom_ar['lk'],
                syntax = syntax,
                changeIn = custom_ar['changeIn'],
            )
            car.items.add(*item_obj_all)

        operation = custom_ar.pop('operation')
        change_in = custom_ar.pop('changeIn')
        items = custom_ar.pop('items')

        cs_exists = True
        for item in items:
            cs_exists = FsAccountLite.objects.get(
                name = item['nm'],
                oc = item['oc']
            ).cs.exists()
            if not cs_exists:
                cs_exists = False
                break

        ars = ArSeries(
            operation = operation,
            change_in = change_in,
            items = items,
        )
        ts = ars.time_series(self.stock_code)
        if len(ts) > 0:
            ts = fill_tgap(ts)
            data = json.dumps({
                'ts': {
                    't': ts.fqe.to_json(orient='records'),
                    'val': ts.value.to_json(orient='records'),
                },
                'cs_exists': cs_exists,
            })
        else:
            data = json.dumps(None)

        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'send.car',
                'text': data
            }
        )

    def get_dist_data(self, custom_ar, tp):
        operation = custom_ar.pop('operation')
        change_in = custom_ar.pop('changeIn')
        items = custom_ar.pop('items')
        ars = ArSeries(
            operation = operation,
            change_in = change_in,
            items = items,
        )

        tp_json = tp
        tp = pd.to_datetime(tp, unit='ms')

        cs = ars.cross_section(self.market, tp)
        cs['rank'] = cs.value.rank(ascending=False, method='min')
        cs['pct'] = cs.value.rank(pct=True, method='min')
        cs['eval'] = pd.cut(
            cs.pct,
            bins = [0, .05, .2, .4, .6, .8, .95, 1],
            labels = ['lowest', 'lower', 'low', 'mid', 'high', 'higher', 'highest'],
        )

        ## stock specific data
        if self.stock_code in cs.stock_code.to_list():
            d = cs.loc[cs.stock_code==self.stock_code].to_dict(orient='records')[0]
        else:
            d = {
                'value': None,
                'rank': None,
                'pct': None,
                'eval': None,
            }

        ## cross sectional distribution
        desc = cs.value.describe().to_dict()

        # winsorize
        # step1. evaluate skewness
        bound_outlier = [.025, .975]
        lb, ub = cs.value.quantile(bound_outlier)
        outliers = (cs.value < lb) | (cs.value > ub)
        sk = skew(cs.value[~outliers])

        # step2. determine truncation side based on skewness
        bound = (
            [.01, .95] if sk >= 2
            else (
                [.05, .99] if sk <= -2
                else [.025, .975]
            )
        )
        # step3. winsorize
        lb, ub = cs.value.quantile(bound)
        trunc = (cs.value >= lb) & (cs.value <=ub)
        cs_trunc = cs[trunc]

        # replace mean with winsorized one
        desc_trunc = cs_trunc.value.describe().to_dict()
        desc['mean'] = desc_trunc['mean']

        # histogram
        bins = list(np.linspace(
            desc_trunc['min'],
            desc_trunc['max'],
            int(desc_trunc['count']),
        ))
        counts = np.histogram(cs_trunc.value, bins)[0]
        counts = [int(c) for c in counts]

        # kde
        kde = get_kde(cs_trunc.value, bins)

        data = json.dumps({
            'tp': tp_json,
            'val': d['value'],
            'rank': d['rank'],
            'pct': d['pct'],
            'eval': d['eval'],
            'avg': desc['mean'],
            'q1': desc['25%'],
            'q2': desc['50%'],
            'q3': desc['75%'],
            'bins': bins,
            'counts': counts,
            'kde': kde,
        })
        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'send.car',
                'text': data
            }
        )


def get_oper_equiv(operation):
    return [operation]
