from .data_visualizers import *
from ggdb.models import *
from ggdb.batchtools.temp import *
from plotly.offline import plot

import plotly.graph_objects as go


class RecentAccountRatio:
    def __init__(self, name, method, market):
        self.name = name
        self.label_kor = AccountRatio.objects.get(name=self.name).labelKor
        self.method = method
        self.market = market
        self.indexes = ['stock_code','corp_name', 'fqe']
        self.corp_all = Corp.objects.filter(delistedAt__isnull=True, market=self.market)

    @property
    def series(self):
        rows = AccountRatioCrossSectionManager().table_rows(self.method, self.market)
        tgcols = self.indexes+[self.name]
        new_rows = []
        for row in rows:
            new_rows.append({c:row[c] for c in tgcols})
        return pd.DataFrame.from_records(new_rows).dropna().set_index(self.indexes)[self.name]

    @property
    def inspect(self):
        sc_all = self.series.index.get_level_values('stock_code')
        missings = [corp for corp in self.corp_all if corp.stockCode not in sc_all]
        return {
            'n_corp_all': self.corp_all.count(),
            'n_obs': len(self.series),
            'missings': missings,
        }

    def describe(self, **kwargs):
        bounds = kwargs.pop('bounds',None)
        if bounds == None:
            desc = self.series.describe()
            outliers = None
        else:
            lb, ub = self.series.quantile(bounds).tolist()
            winsor = (self.series >= lb) & (self.series <= ub)
            desc = self.series[winsor].dropna().describe()
            sc_outliers = self.series[~winsor].dropna().index.get_level_values('stock_code')
            outliers = [corp for corp in self.corp_all if corp.stockCode in sc_outliers]

        lk = {
            'count': '종목수',
            'mean': '평균',
            'std': '표준편차',
            'min': '최소',
            '25%': '1분위',
            '50%': '중위',
            '75%': '3분위',
            'max': '최대'
        }

        return {
            'desc': desc.rename(index=lk).to_dict(),
            'outliers': outliers
        }

    def histogram(self, **kwargs):
        bounds = kwargs.pop('bounds',None)
        if bounds == None:
            s = self.series
        else:
            print(self.series)
            lb, ub = self.series.quantile(bounds).tolist()
            winsor = (self.series >= lb) & (self.series <= ub)
            s = self.series[winsor].dropna()

        method_lk = '연결' if self.method == 'CFS' else '별도'
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=s,
            histnorm='probability',
            name = self.label_kor
        ))
        fig.update_layout(
            # autosize = False,
            # width = 500,
            # height = 400,
            paper_bgcolor='rgba(0,0,0,0)',
            # plot_bgcolor='rgba(0,0,0,0)',
            margin = dict(l=30,r=30,b=30,t=30),
            # barmode='overlay',
            # x=f"{self.label_kor}",
            # y="확률밀도",
            title_text=f"{self.market} {self.label_kor} 분포 ({method_lk})"
        )
        fig.update_traces(opacity=.75)
        return plot(fig, output_type='div')


class IndicatorsViewManager:
    def __init__(self):
        self.SORT_ORDER_AR = {
            '안정성': 0,
            '수익성': 1,
            '성장성 및 활동성': 2,
        }

    def sidebar(self):
        ar_all = sorted(
            AccountRatio.objects.all().values(),
            key = lambda ar: self.SORT_ORDER_AR[ar['div']]
        )
        ar_data = []
        prev_div = None
        for ar in ar_all:
            if ar['div'] != prev_div:
                ar_data.append({'is_button': False, 'div_name': ar['div']})
            ar_data.append({'is_button': True, **ar})
            prev_div = ar['div']
        return {
            'accountRatio': {
                'label_kor': '재무비율',
                'rows': ar_data,
            },
        }

    def main(self, request):
        if request.method == 'POST':
            if request.POST['clsSelected'] == 'accountRatio':
                oc_mkt_ord = [('CFS', 'KOSPI'), ('OFS', 'KOSPI'), ('CFS', 'KOSDAQ'), ('OFS', 'KOSDAQ')]
                if request.POST['itemSelected'] == 'crossSectionAll':
                    arcsm = AccountRatioCrossSectionManager()
                    return {
                        'status': 'view_ar_all',
                        'data':{
                            f"{oc}_{mkt}": {
                                'header': arcsm.table_header(oc, mkt),
                                'rows': arcsm.table_rows(oc, mkt),
                            } for oc, mkt in oc_mkt_ord
                        }
                    }
                else:
                    view_ar_data = {}
                    for oc, mkt in oc_mkt_ord:
                        recent_ar = RecentAccountRatio(
                            request.POST['itemSelected'],
                            oc,
                            mkt
                        )
                        view_ar_data[f"{oc}_{mkt}"] = {
                            'series': recent_ar.series,
                            'inspect': recent_ar.inspect,
                            'desc': recent_ar.describe(bounds=[.025, .975]),
                            'hist': recent_ar.histogram(bounds=[.025, .975]),
                        }
                    return {
                        'status': 'view_ar',
                        'account_ratio': AccountRatio.objects.get(name=request.POST['itemSelected']),
                        'data': view_ar_data,
                    }
        else:
            arcsm = AccountRatioCrossSectionManager()
            return {
                'status': 'view_ar_all',
                'data':{
                    f"{oc}_{market}": {
                        'header': arcsm.table_header(oc, market),
                        'rows': arcsm.table_rows(oc, market),
                    } for oc, market in [
                        ('CFS','KOSPI'),
                        ('OFS','KOSPI'),
                        ('CFS','KOSDAQ'),
                        ('OFS','KOSDAQ'),
                    ]
                }
            }
