from .fa import FaSeries
from .tools import *
from ggdb.models import Corp, FsAccount, FsDetail

import numpy as np
import pandas as pd
import re

class ArSeries:
    def __init__(self, ar_syntax, change_in, oc):
        # self.mkt = Corp.objects.get(stockCode=stock_code).market
        self.arg_all = re.findall('`(.*?)`', ar_syntax)
        strargs = str(self.arg_all)[1:-1].replace("'","")
        strfunc = f"lambda {strargs}:" + ar_syntax.replace("`","")
        self.operation = eval(strfunc)
        self.oc = oc
        self.change_in = change_in

    def time_series(self, stock_code):
        s_all = []
        for acnt_nm in self.arg_all:
            s = FaSeries(acnt_nm, self.oc).time_series(stock_code)
            if len(s) > 0:
                s_all.append(s.set_index('fqe').rename(columns={'value':acnt_nm}))
            else:
                return pd.DataFrame()
        df = pd.concat(s_all, axis=1)
        ts = (
            self.operation(*[df[c] for c in self.arg_all])
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
                    FaSeries(acnt_nm, self.oc)
                    .cross_section(mkt, ttp)
                    .set_index(['stock_code','corp_name','fqe'])
                    .rename(columns={'value':acnt_nm})
                    ) for acnt_nm in self.arg_all
                ], axis=1)
                cs_all.append(
                    self.operation(*[df[c] for c in self.arg_all])
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
                FaSeries(acnt_nm, self.oc)
                .cross_section(mkt, tp)
                .set_index(['stock_code','corp_name','fqe'])
                .rename(columns={'value':acnt_nm})
                ) for acnt_nm in self.arg_all
            ], axis=1)
            cs = (
                self.operation(*[df[c] for c in self.arg_all])
                .rename('value')
                .replace([-np.inf,np.inf],np.nan)
                .dropna()
                .reset_index()
            )
            return cs
