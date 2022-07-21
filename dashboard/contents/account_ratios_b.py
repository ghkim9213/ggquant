from dashboard.models import *

import numpy as np
import pandas as pd
import time


def set_label_kor(label_kor):
    def decorator(f):
        f.__dict__['label_kor'] = label_kor
        return f
    return decorator


# get recent version of account tree
class AccountRatios:

    def __init__(self):
        self._name = 'account-ratios'
        self._label_kor = '재무비율'
        self._fsinfo = {
            # 'fs__type__name': 'fsType',
            'fs__by': 'by',
            'fs__bq': 'bq',
        }
        self._corpinfo = {
            'fs__corp__fye': 'fye',
            'fs__corp__market': 'market',
            'fs__corp__industry': 'industry',
            'fs__corp__stockCode': 'stkCd',
            'fs__corp__corpName': 'corpNm',
        }
        self._common_fields = list(self._fsinfo.keys()) + ['account__accountNm', 'value']
        # self._is_one2many = lambda s: 0 in s.unstack('fsType').isnull().astype(int).sum(axis=1).unique()

    # @set_label_kor('유동비율')
    # def ca2cl(self, **kwargs):
    #
    #     # (step1) set inputs to query data
    #     all = kwargs.pop('all','')
    #
    #     # filters, filters and indices
    #     filters = {
    #         'fs__type__name__in': ['BS1', 'BS2'],
    #         'fs__corp__listedAt__isnull': False,
    #         'account__accountNm__in': ['CurrentAssets','CurrentLiabilities'],
    #     }
    #     fields = self._common_fields
    #     if all == True:
    #         fields = fields + list(self._corpinfo.keys())
    #     else:
    #         stockCode = kwargs.pop('stockCode','')
    #         filters['fs__corp__stockCode'] = stockCode
    #
    #     indices = [f for f in fields if f != 'value']
    #
    #     # (step2) query data
    #     # t0 = time.time()
    #     return query_df_fd(filters=filters, fields=fields, indices=indices)

    @set_label_kor('유동비율')
    def ca2cl(self, **kwargs):

        # (step1) set inputs to query data
        all = kwargs.pop('all','')

        # filters, filters and indices
        filters = {
            'fs__type__name__in': ['BS1', 'BS2'],
            'fs__corp__listedAt__isnull': False,
            'account__accountNm__in': ['CurrentAssets','CurrentLiabilities'],
        }
        fields = self._common_fields
        if all == True:
            fields = fields + list(self._corpinfo.keys())
        else:
            stockCode = kwargs.pop('stockCode','')
            filters['fs__corp__stockCode'] = stockCode

        indices = [f for f in fields if f != 'value']

        # (step2) query data
        t0 = time.time()

        qs = (
            F
        )
        df = query_df_fd(filters=filters, fields=fields, indices=indices)
        t1 = time.time()
        print(f"query data as df: {t1-t0}")
        # df = df.unstack('account__accountNm')

        # (step3) get value
        s = (df[('value','CurrentAssets')]/df[('value','CurrentLiabilities')])
        t2 = time.time()
        print(f"get value: {t2-t1}")

        # return s
        # (step4) rearrange data to display
        is_one2many = 0 in s.unstack('fs__type__name').isnull().astype(int).sum(axis=1).unique()
        rename_map = {**self._fsinfo, **self._corpinfo}
        if is_one2many:
            uniq_ft = s.index.get_level_values('fs__type__name').unique()
            return {f"result-{ft}": s2table_data(s[ft],ascending=False,rename_map=rename_map) for ft in uniq_ft}
        else:
            return {'result': s2table_data(s, ascending=False, rename_map=rename_map)}


    @set_label_kor('부채비율')
    def l2eatoop(self, **kwargs):

        # (step1) set inputs to query data
        all = kwargs.pop('all','')

        # filters, filters and indices
        filters = {
            'fs__type__name__in': ['BS1', 'BS3'],
            'fs__corp__listedAt__isnull': False,
            'account__accountNm__in': ['Liabilities','EquityAttributableToOwnersOfParent'],
        }
        fields = self._common_fields
        if all == True:
            fields = fields + list(self._corpinfo.keys())
        else:
            stockCode = kwargs.pop('stockCode','')
            filters['fs__corp__stockCode'] = stockCode

        indices = [f for f in fields if f != 'value']

        # (step2) query data
        t0 = time.time()
        df = query_df_fd(filters=filters, fields=fields, indices=indices)
        t1 = time.time()
        print(f"query data as df: {t1-t0}")
        # df = df.unstack('account__accountNm')

        # (step3) get value
        s = (df[('value','Liabilities')]/df[('value','EquityAttributableToOwnersOfParent')])
        t2 = time.time()
        print(f"get value: {t2-t1}")

        # (step4) rearrange data to display
        # is_one2many = 0 in s.unstack('fsType').isnull().astype(int).sum(axis=1).unique()
        # if is_one2many:
        rename_map = {**self._fsinfo, **self._corpinfo}
        return s.rename('value')#.reset_index().rename(columns=rename_map).set_index(indices)


    # @set_label_kor('부채비율')
    # def l2eatoop(self, **kwargs):
    #     all = kwargs.pop('all','')
    #
    #     fields = (
    #         list(self._fsinfo.keys())
    #         + ['account__accountNm', 'value']
    #     )
    #
    #     if all == True:
    #         fields = fields + list(self._corpinfo.keys())
    #     else:
    #         stockCode = kwargs.pop('stockCode','')
    #         filters['fs__corp__stockCode'] = stockCode
    #
    #     indices = [f for f in fields if f != 'value']
    #     df = query_df_fd(filters=filters, fields=fields, indices=indices)
    #     # df = df.unstack('account__accountNm')
    #
    #     rename_map = {**self._fsinfo, **self._corpinfo}
    #     return s.rename('value').reset_index().rename(columns=rename_map)


    # @set_label_kor('부채비율')
    # def tl2eo(self, **kwargs):
    #     all = kwargs.pop('all','')
    #     fields = [
    #         'fs__by', 'fs__bq', 'fs__type__name',
    #         'account__accountNm', 'value',
    #     ]
    #     if all == True:
    #         fields = ['fs__corp__stockCode', 'fs__corp__corpName'] + fields
    #     else:
    #         stockCode = kwargs.pop('stockCode','')
    #         filters['fs__corp__stockCode'] = stockCode
    #
    #     indices = fields[:-1]
    #     df = query_df_fd(filters=filters, fields=fields, indices=indices)
    #     df = df.unstack('account__accountNm')
    #     s = (df[('value','Liabilities')]/df[('value','EquityAttributableToOwnersOfParent')])#.unstack('fs__type__name')
    #     rename_map = {
    #         'fs__corp__stockCode': 'stkCd',
    #         'fs__corp__corpName': 'corpNm',
    #         'fs__type__name': 'fsType',
    #         'fs__by': 'by',
    #         'fs__bq': 'bq',
    #     }
    #     return s.rename('value').reset_index().rename(columns=rename_map).to_dict(orient='records')



def get_ar_elements(**kwargs):
    qs = (
        FsDetail.objects
        .select_related('fs','fs__corp','fs__type','account')
        .filter(**filters)
    ).order_by('fs__id','account__id')
    return


def query_df_fd(**kwargs):
    t0 = time.time()
    qs = (
        FsDetail.objects.filter(**kwargs['filters'])
        .select_related('fs','fs__corp','fs__type','account')
    )
    t1 = time.time()
    print(f"{t1-t0} sec for django query")
    df = pd.DataFrame.from_records(qs.values(*kwargs['fields']))
    t2 = time.time()
    print(f"{t2-t1} sec to convert django queryset to pd df")
    df = df.drop_duplicates(kwargs['indices']).set_index(kwargs['indices']).unstack('account__accountNm')
    t3 = time.time()
    print(f"{t3-t2} sec to beautifulize df")
    # df = df.sort_values(['fs__by','fs__bq'],ascending=[False,False])
    return df
    # return df.drop_duplicates(kwargs['indices']).set_index(kwargs['indices']).unstack('account__accountNm')


def s2table_data(s,**kwargs):
    ascending = kwargs.pop('ascending')
    rename_map = kwargs.pop('rename_map')
    s = s.unstack(['fs__by','fs__bq']).round(2)
    colord = s.columns.sortlevel(ascending=False)[0]
    latest = colord[0]
    s = s[colord].sort_values(latest,ascending=ascending)
    s.columns = [f"{x[0]}q{x[1]}" for x in s.columns]
    df = s.replace({np.nan:None,np.inf:None}).reset_index().rename(columns=rename_map)
    return {
        'header': df.columns.tolist(),
        'rows': df.values.tolist(),
    }

# def is_one2many(s)
# def reshape_s(s):
#     s.rename('value')
