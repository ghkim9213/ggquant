from .data_visualizers import *

from collections import Counter
from ggdb.models import *
from ggdb.batchtools.account_ratio import *
from plotly.offline import plot

import plotly.graph_objects as go


class LatestAccountRatioSeries:
    def __init__(self, oc, mkt, ar):
        larm = LatestAccountRatioManager()
        self.method = oc
        self.market = mkt
        self.ar = ar
        self.data = larm.read_temp(oc, mkt, ar=ar)
        self._series = None
        self.corp_all = Corp.objects.filter(market=self.market, delistedAt__isnull=True)
        self._search_data = []

    @property
    def cleaned_data(self):
        cleaned_data = self.data.copy()
        stock_code_all = [d['stock_code'] for d in self.data]

        # additional missings
        for corp in self.corp_all:
            if corp.stockCode not in stock_code_all:
                cleaned_data.append({
                    'stock_code': corp.stockCode,
                    'corp_name': corp.corpName,
                    'by': None,
                    'bq': None,
                    'value': None,
                })
        return cleaned_data

    def inspect(self, **kwargs):
        missings = [d for d in self.cleaned_data if d['value'] == None]
        self._search_data += [{
            **d,
            'rank': None,
            'rankpct': None,
            'is_missing': True,
            'is_outlier': None
        } for d in missings]
        valid_rows = [d for d in self.cleaned_data if d['value'] != None]
        s = (
            pd.DataFrame.from_records(valid_rows)
            .set_index(['stock_code', 'corp_name', 'by', 'bq'])
            .value
        )

        bounds = kwargs.pop('bounds', None)
        if bounds == None:
            self._series = s
            outliers = None
            df = s.reset_index()
            df['rank'] = df.value.rank(ascending=False, method='min')
            df['rankpct'] = df.value.rank(ascending=False, pct=True, method='min').round(4) * 100
            self._search_data += [{
                **d,
                'is_missing': False,
                'is_outlier': None,
            } for d in df.to_dict(orient='records')]
        else:
            lb, ub = s.quantile(bounds).tolist()
            winsor = (s >= lb) & (s <= ub)

            # outliers
            outliers = s[~winsor].reset_index().to_dict(orient='records')
            self._search_data += [{
                **d,
                'rank': None,
                'rankpct': None,
                'is_missing': False,
                'is_outlier': True
            } for d in s[~winsor].reset_index().to_dict(orient='records')]

            # valids
            self._series = s[winsor]
            df = s[winsor].reset_index()
            df['rank'] = df.value.rank(ascending=False, method='min')
            df['rankpct'] = df.value.rank(ascending=False, pct=True, method='min').round(4) * 100
            self._search_data += [{
                **d,
                'is_missing': False,
                'is_outlier': False
            } for d in df.to_dict(orient='records')]

        return {
            'corp_all': self.corp_all,
            'missings': {
                'count': len(missings),
                'data': missings,
            },
            'outliers': {
                'count': len(outliers),
                'data': outliers,
            },
        }

    def describe(self):
        if self._series is not None:
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
            return self._series.describe().rename(index=lk).to_dict()
        else:
            raise ValueError('self._series is empty. self.inspect() should be preceded to self.describe().')

    def histogram(self):
        if self._series is not None:
            method_lk = '연결' if self.method == 'CFS' else '별도'
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=self._series,
                histnorm='probability',
                name = self.ar.labelKor
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                margin = dict(l=30,r=30,b=30,t=30),
                title_text=f"{self.market} {self.ar.labelKor} 분포 ({method_lk})"
            )
            fig.update_traces(opacity=.75)
            return plot(fig, output_type='div')
        else:
            raise ValueError('self._series is empty. self.inspect() should be preceded to self.histogram().')

class IndicatorsViewManager:
    def __init__(self):
        self.ar_all = AccountRatio.objects.all()
        self.SORT_ORDER_AR = {
            '안정성': 0,
            '수익성': 1,
            '성장성 및 활동성': 2,
        }

    def sidebar(self):
        ar_all = sorted(
            self.ar_all.values(),
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
                larm = LatestAccountRatioManager()
                if request.POST['itemSelected'] == 'latestAccountRatioAll':
                    view_lar_all_data = {}
                    for oc, mkt in oc_mkt_ord:
                        # get data for table rows
                        table_rows = larm.read_temp(oc, mkt)

                        # get data for table header
                        header_all = [self.ar_all.get(name=ar_nm) for ar_nm in list(table_rows[0].keys())[4:]]
                        lk_all = [h.labelKor for h in header_all]
                        div_counter = Counter([h.div for h in header_all])
                        table_header0 = f'''
                            <tr>
                                <th rowspan="2">종목코드</th>
                                <th rowspan="2">종목명</th>
                                <th rowspan="2">회계연도</th>
                                <th rowspan="2">분기</th>
                                <th colspan="{div_counter['안정성']}">안정성</th>
                                <th colspan="{div_counter['수익성']}">수익성</th>
                                <th colspan="{div_counter['성장성 및 활동성']}">성장성 및 활동성</th>
                            </tr>
                        '''
                        table_header1 = ""
                        for lk in lk_all:
                            table_header1 += f"<th>{lk}</th>"
                        table_header1 = f"<tr>{table_header1}</tr>"
                        table_header = table_header0 + table_header1
                        view_lar_all_data[f"{oc}_{mkt}"] = {
                            'header': table_header,
                            'rows': table_rows,
                        }

                    return {
                        'status': 'view_lar_all',
                        'data': view_lar_all_data,
                    }
                else:
                    ar = self.ar_all.get(name=request.POST['itemSelected'])
                    view_lar_data = {
                        'account_ratio': ar,
                        'results': {}
                    }
                    for oc, mkt in oc_mkt_ord:
                        try:
                            lars = LatestAccountRatioSeries(oc, mkt, ar)
                        except KeyError:
                            continue

                        # lars_inspect =
                        view_lar_data['results'][f"{oc}_{mkt}"] = {
                            'inspect': lars.inspect(bounds=[.025,.975]),
                            'desc': lars.describe(),
                            'hist': lars.histogram(),
                            'search_data': json.dumps(lars._search_data),
                            # 'series': lars._series.reset_index().to_json(orient='records'),
                            # 'desc': {
                            #     'n_corp': len(recent_ar.df),
                            #     'n_miss': recent_ar.df.is_missing.sum(),
                            #     'n_outlier': recent_ar.df.is_outlier.sum(),
                            #     'stats': recent_ar.describe(winsorize=True),
                            #     'hist': recent_ar.histogram(winsorize=True),
                            # },
                            # 'search_data': recent_ar.df.to_json(orient='records'),
                        }
                    return {
                        'status': 'view_lar',
                        'data': view_lar_data,
                    }
        else:
            # arcsm = AccountRatioCrossSectionManager()
            return None


# def get_view_lar_content(lar_data):
