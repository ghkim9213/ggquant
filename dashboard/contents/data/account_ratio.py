from ggdb.models import AccountRatio
import pandas as pd

import plotly.graph_objects as go

class AccountRatioSeries:

    def __init__(self, ar_nm, oc, mkt):
        ar = AccountRatio.objects.get(name=ar_nm)
        FIELDS = {
            'corp__stockCode': 'stock_code',
            'corp__corpName': 'corp_name',
            'fqe': 'fqe',
            'value': 'value',
        }
        qs = ar.values.filter(
            oc = oc,
            corp__market = mkt,
        ).select_related('corp')

        if not qs.exists():
            raise KeyError(f"No such account ratio '{ar.name}' for {oc}_{mkt}.")

        self.panel = (
            pd.DataFrame
            .from_records(qs.values(*FIELDS.keys()))
            .rename(columns=FIELDS)
        )
        self.panel.fqe = pd.to_datetime(self.panel.fqe)

    def get_cross_section(self, timestamp):
        return (
            self.panel
            .loc[self.panel['fqe'] <= timestamp]
            .sort_values(['stock_code', 'fqe'])
            .groupby('stock_code').last()
            .reset_index()
        )

    def get_time_series(self, stock_code):
        ts = (
            self.panel
            .loc[self.panel.stock_code==stock_code]
            .reset_index(drop=True)
        )
        if len(ts) == 0:
            raise KeyError(f"Values for {stock_code} not found.")
        else:
            return ts
