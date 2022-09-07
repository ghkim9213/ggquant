from .data.account_ratio import AccountRatioSeries

from ggdb.models import Corp, AccountRatio
from scipy.stats import gaussian_kde, skew

import json
import numpy as np
import pandas as pd

class ArPanel:
    def __init__(self, ar_nm, oc, stock_code):
        self.corp = Corp.objects.get(stockCode=stock_code)
        self.ar_lk = AccountRatio.objects.get(name=ar_nm).labelKor
        self.ars = AccountRatioSeries(ar_nm, oc, self.corp.market)
        self.ts = self.ars.get_time_series(self.corp.stockCode)
        self._dateformatter = lambda tp: f"{tp.year}-{str(tp.month).zfill(2)}-{str(tp.day).zfill(2)}"
        self._hex_to_rgba = lambda h, opacity: (
            f"rgba{tuple([int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)] + [opacity])}"
        )
        self._graph_data = None
        self._table_data = None
        # self._global_props = None

    def update_table_data(self):
        self._table_data = []

        # add distribution data for each timepoint
        for tp in self.ts.fqe.sort_values():
            val = self.ts.loc[self.ts.fqe == tp].value
            cs = self.ars.get_cross_section(tp)
            cs['rank'] = cs.value.rank(ascending=False, method='min')
            cs['pct'] = cs.value.rank(pct=True, method='min')
            cs['status'] = pd.cut(
                cs.pct,
                bins = [0, .05, .2, .4, .6, .8, .95, 1],
                # labels = ['highest', 'higher', 'high', 'mid', 'low', 'lower', 'lowest'],
                labels = ['lowest', 'lower', 'low', 'mid', 'high', 'higher', 'highest'],                
            )
            d = cs.loc[cs.stock_code==self.corp.stockCode].to_dict(orient='records')[0]
            d['fqe'] = int(d['fqe'].timestamp() * 1000) # pd timestampe to js timestamp
            self._table_data.append(d)

    def update_graph_data(self):
        # reset data for figure
        self._graph_data = {}

        # time horizon
        self._graph_data['tp_all'] = [td['fqe'] for td in self._table_data]

        # evaluate skewness
        bound_outlier = [.025, .975]
        lb, ub = self.ars.panel.value.quantile(bound_outlier)
        outliers = (self.ars.panel.value < lb) | (self.ars.panel.value > ub)
        sk = skew(self.ars.panel.value[~outliers])

        # determine truncation side based on skewness
        bound = (
            [.01, .95] if sk >= 2
            else (
                [.05, .99] if sk <= -2
                else [.025, .975]
            )
        )

        # update self._graph_data
        gmax, gmin = None, None
        val_all = self.ts.value.tolist()
        avg_all, q1_all, q2_all, q3_all = [], [], [], []
        cs_all = []
        for tp in self.ts.fqe.sort_values():
            cs = self.ars.get_cross_section(tp)

            desc = cs.value.describe().to_dict()
            q1_all.append(desc['25%'])
            q2_all.append(desc['50%'])
            q3_all.append(desc['75%'])

            lb, ub = cs.value.quantile(bound)
            trunc = (cs.value >= lb) & (cs.value <= ub)
            avg_all.append(cs[trunc].value.mean())

            cs_all.append(cs[trunc].value.tolist())

            lmax = cs[trunc].value.max()
            lmin = cs[trunc].value.min()
            if not gmax:
                gmax = lmax
            elif gmax < desc['max']:
                gmax = lmax
            if not gmin:
                gmin = lmin
            elif gmin > desc['min']:
                gmin = lmin

        self._graph_data['ts'] = {
            'val': val_all,
            'avg': avg_all,
            'q1': q1_all,
            'q2': q2_all,
            'q3': q3_all,
        }

        count_all = [len(cs) for cs in cs_all]
        bins = list(np.linspace(
            gmin, gmax,
            int(sum(count_all)/len(count_all))
        ))

        pm_all = [list(get_prob_mass(s, bins)) for s in cs_all]
        kde_all = [list(get_norm_kde(s, bins)) for s in cs_all]

        self._graph_data['dist'] = {
            'bins': bins,
            'pm': pm_all,
            'kde': kde_all,
        }


    def get_data(self, **kwargs):
        return json.dumps({
            'table': self._table_data,
            'graph_data': self._graph_data,
        })

def get_prob_mass(s, bins):
    return np.histogram(s, bins)[0] / len(s)

def get_norm_kde(s, bins):
    kernel = gaussian_kde(s)
    kde = kernel(bins)
    return kde / kde.sum()
