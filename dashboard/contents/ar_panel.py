from .data.ar import ArSeries
from .data.tools import *
from .tools import *

from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
from ggdb.models import Corp, AccountRatio

import json
import numpy as np
import pandas as pd

class ArPanel:
    def __init__(self, stock_code, channel_name):
        self.channel_layer = get_channel_layer()
        self.channel_name = channel_name

        self.stock_code = stock_code
        self.market = Corp.objects.get(stockCode=stock_code).market

    def get_ts_data(self, ar):
        operation = ar.pop('operation')
        change_in = ar.pop('changeIn')
        items = ar.pop('items')

        ars = ArSeries(
            operation = operation,
            change_in = change_in,
            items = items
        )
        ts = ars.time_series(self.stock_code)
        if len(ts) > 0:
            ts = fill_tgap(ts)
            data = json.dumps({
                'ts': {
                    't': ts.fqe.to_json(orient='records'),
                    'val': ts.value.to_json(orient='records'),
                },
                'cs_exists': True,
            })
        else:
            data = json.dumps(None)

        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'send.arp',
                'text': data
            }
        )

    def get_dist_data(self, ar, tp):
        operation = ar.pop('operation')
        change_in = ar.pop('changeIn')
        items = ar.pop('items')
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
                'type': 'send.arp',
                'text': data
            }
        )
