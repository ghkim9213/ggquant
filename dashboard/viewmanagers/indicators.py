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

        corp_all = Corp.objects.filter(delistedAt__isnull=True, market=self.market)
        rows = AccountRatioCrossSectionManager().table_rows(self.method, self.market)
        if self.name in rows[0].keys():
            tgcols = self.indexes+[self.name]
            new_rows = []
            for row in rows:
                new_rows.append({c:row[c] for c in tgcols})

            df_corp_all = (
                pd.DataFrame.from_records(
                    [{
                        'stock_code':corp.stockCode,
                        'corp_name':corp.corpName
                    } for corp in corp_all]
                )#.set_index(self.indexes[:-1])
            )
            df_value = pd.DataFrame.from_records(new_rows).dropna()
            self.df = (
                df_corp_all.merge(
                    df_value,
                    on=['stock_code','corp_name'],
                    how='left')
            ).rename(columns={self.name:'value'})
        else:
            raise ValueError(f"{self.method} {self.market} has no attribute of {self.name}.")

    def inspect(self, **kwargs):
        self.df['is_missing'] = self.df.value.isnull()
        self.df['rank'] = self.df.value.rank(ascending=False, method='min')
        self.df['rankpct'] = self.df.value.rank(ascending=False, pct=True, method='min').round(4) * 100
        outliers = None
        bounds = kwargs.pop('bounds',None)
        if bounds != None:
            s = self.df.dropna().set_index(self.indexes).value
            lb, ub = s.quantile(bounds).tolist()
            winsor = (s >= lb) & (s <= ub)
            self.df = pd.concat(
                [
                    self.df.set_index(self.indexes),
                    (~winsor).rename('is_outlier')
                ], axis=1
            ).reset_index()

    def describe(self, **kwargs):
        winsorize = kwargs.pop('winsorize', None)
        df = self.df.loc[self.df.is_missing==False]
        df = df.loc[df.is_outlier==False] if winsorize == True else self.df
        s = df.set_index(self.indexes).value.dropna()
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
        return s.describe().rename(index=lk).to_dict()

    def histogram(self, **kwargs):
        winsorize = kwargs.pop('winsorize', None)
        df = self.df.loc[(self.df.is_missing==False)&(self.df.is_outlier==False)] if winsorize == True else self.df
        s = df.set_index(self.indexes).value.dropna()
        method_lk = '연결' if self.method == 'CFS' else '별도'
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=s,
            histnorm='probability',
            name = self.label_kor
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            margin = dict(l=30,r=30,b=30,t=30),
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
                    view_ar_data = {
                        'account_ratio': AccountRatio.objects.get(name=request.POST['itemSelected']),
                        'results': {}
                    }
                    for oc, mkt in oc_mkt_ord:
                        try:
                            recent_ar = RecentAccountRatio(
                                request.POST['itemSelected'],
                                oc,
                                mkt
                            )
                        except ValueError:
                            continue
                        recent_ar.inspect(bounds=[.025,.975])
                        view_ar_data['results'][f"{oc}_{mkt}"] = {
                            'desc': {
                                'n_corp': len(recent_ar.df),
                                'n_miss': recent_ar.df.is_missing.sum(),
                                'n_outlier': recent_ar.df.is_outlier.sum(),
                                'stats': recent_ar.describe(winsorize=True),
                                'hist': recent_ar.histogram(winsorize=True),
                            },
                            'search_data': recent_ar.df.to_json(orient='records'),
                        }
                    return {
                        'status': 'view_ar',
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
