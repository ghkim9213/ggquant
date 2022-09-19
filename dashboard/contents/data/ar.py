from .fa import FaSeries
from .tools import *
from ggdb.models import Corp
from ggdb.models import FsAccountLite

import numpy as np
import pandas as pd
import re

class ArSeries:
    def __init__(self, operation, change_in, items):
        letter_all = re.findall('[^\/\+\(\)\*\-]', operation)
        letter_uniq = list(set(letter_all))
        strfunc = f"lambda {','.join(letter_uniq)}: {operation}"
        # self.input_order = letter_uniq
        input_order = {v: i for i, v in enumerate(letter_uniq)}
        self.operation = eval(strfunc)
        self.change_in = change_in
        self.items = sorted(items, key=lambda x: input_order[x['letter']])

    def time_series(self, stock_code):
        s_all = []
        for item in self.items:
            s = FaSeries(item['nm'], item['oc']).time_series(stock_code)
            if len(s) > 0:
                s_all.append(s.set_index('fqe').rename(columns={'value':item['letter']}))
            else:
                return pd.DataFrame()
        df = pd.concat(s_all, axis=1)
        ts = (
            self.operation(*[df[item['letter']] for item in self.items])
            .rename('value')
            .replace([-np.inf,np.inf],np.nan)
            .dropna()
            .reset_index()
        )

        # fill time period
        ts = fill_tgap(ts)

        if self.change_in:
            ts['growth'] = ts.value / ts.value.shift(1)
            return ts[['fqe','growth']].rename(columns={'growth': 'value'})
        else:
            return ts[['fqe','value']]

    def cross_section(self, mkt, tp):
        if self.change_in:
            prev_tp = prev_yq(tp)
            cs_all = []
            for ttp in [prev_tp, tp]:
                df = pd.concat([(
                    FaSeries(item['nm'], item['oc'])
                    .cross_section(mkt, ttp)
                    .set_index(['stock_code','corp_name','fqe'])
                    .rename(columns={'value':item['letter']})
                    ) for item in self.items
                ], axis=1)
                cs_all.append(
                    self.operation(*[df[item['letter']] for item in self.items])
                    .rename('value')
                    .replace([-np.inf,np.inf],np.nan)
                    .dropna()
                )
            panel = pd.concat(cs_all,axis=0).reset_index()
            stock_count = panel.stock_code.value_counts().to_dict()
            valid_stock_code = [k for k, v in stock_count.items() if v == 2]
            panel = panel.loc[panel.stock_code.isin(valid_stock_code)]
            panel = panel.sort_values(['stock_code','fqe'])
            panel['growth'] = panel.value / panel.value.shift(1)
            panel = panel.sort_values(['stock_code','fqe'], ascending=[True,False])
            cs_change_in = panel.drop_duplicates('stock_code')
            return (
                cs_change_in[['stock_code','corp_name','fqe','growth']]
                .rename(columns={'growth': 'value'})
            )
        else:
            df = pd.concat([(
                FaSeries(item['nm'], item['oc'])
                .cross_section(mkt, tp)
                .set_index(['stock_code','corp_name','fqe'])
                .rename(columns={'value':item['letter']})
                ) for item in self.items
            ], axis=1)
            cs = (
                self.operation(*[df[item['letter']] for item in self.items])
                .rename('value')
                .replace([-np.inf,np.inf],np.nan)
                .dropna()
                .reset_index()
            )
            return cs
