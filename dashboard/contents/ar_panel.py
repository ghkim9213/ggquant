from .data.ar import ArSeries
from .data.tools import *

from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
from ggdb.models import Corp, AccountRatio
from scipy.stats import gaussian_kde, skew

import json
import numpy as np
import pandas as pd

class ArPanel:
    def __init__(self, ar_nm, oc, stock_code, channel_name):
        self.channel_layer = get_channel_layer()
        self.channel_name = channel_name

        self.stock_code = stock_code
        self.market = Corp.objects.get(stockCode=stock_code).market

        ar = AccountRatio.objects.get(name=ar_nm)
        self.ars = ArSeries(
            ar_syntax = ar.syntax,
            change_in = ar.changeIn,
            oc = oc
        )

    def generate_static_data(self):
        ts = self.ars.time_series(self.stock_code)
        if len(ts) > 0:
            ts = fill_tgap(ts)
            data = json.dumps({
                't': ts.fqe.to_json(orient='records'),
                'val': ts.value.to_json(orient='records'),
            })
        else:
            data = json.dumps(None)

        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'ar.static',
                'text': data
            }
        )

    def generate_dynamic_data(self, tp):
        tp_json = tp
        tp = pd.to_datetime(tp, unit='ms')
        cs = self.ars.cross_section(self.market, tp)
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
        norm_kde = get_norm_kde(cs_trunc.value, bins)

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
            'kde': norm_kde,
        })
        async_to_sync(self.channel_layer.send)(
            self.channel_name, {
                'type': 'ar.dynamic',
                'text': data
            }
        )

# def get_prob_mass(s, bins):
#     return np.histogram(s, bins)[0] / len(s)

def get_norm_kde(s, bins):
    kernel = gaussian_kde(s)
    kde = kernel(bins)
    return list(kde / kde.sum())
