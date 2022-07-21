from dashboard.models import *
from functools import reduce

import numpy as np
import pandas as pd
import itertools, re, time


class AccountRatio:
    template_pid = 'account-ratio'


    def __init__(self, ar_name, ar_label_kor, ar_syntax):
        self._name = ar_name
        self._label_kor = ar_label_kor
        self._arg_all = re.findall('`(.*?)`', ar_syntax)
        strargs = str(self._arg_all)[1:-1].replace("'","")
        strfunc = f'lambda {strargs}:' + ar_syntax.replace("`","")
        self._calculator = eval(strfunc)
        self._fields = {
            'fs__corp__stockCode': 'stock_code',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'fs__type__name': 'fstype',
            'account__accountNm': 'account_nm',
            'value': 'value',
        }
        self._qs = (
            FsDetail.objects
            .select_related('fs', 'fs__corp', 'fs__type', 'account')
            .filter(
                fs__corp__listedAt__isnull = False,
                account__accountNm__in = self._arg_all,
            )
        )

    def inspect(self):
        # load data
        df = pd.DataFrame.from_records(self._qs.values(*self._fields.keys())).rename(columns=self._fields)
        indexes4dup = [c for c in df.columns if c != 'value']
        df = df.drop_duplicates(indexes4dup)

        # inspect inputs
        indexes_inputs = ['stock_code','by','bq']
        result_inputs = {}
        for a in self._arg_all:
            dfa = df.loc[df.account_nm==a]
            dfa = dfa.groupby(indexes_inputs).fstype.value_counts().unstack('fstype')
            is_single_type = len(dfa.columns) == 1
            is_mixed_type = (not is_single_type) & ((dfa.fillna(0).sum(axis=1) > 1).sum() == 0)
            result_inputs[a] = {
                'in': dfa.columns.tolist(),
                'is_single_type': is_single_type,
                'is_mixed_type': is_mixed_type,
            }

        # inspect outputs
        ft_choices = [x['in'] if x['is_mixed_type'] == False else [None] for x in result_inputs.values()]
        ft_comb_all = list(itertools.product(*ft_choices))
        result_outputs = {
                f"comb{i}": {
                'comb': dict(zip(result_inputs.keys(),v)),
                'desc': None,
            } for i, v in enumerate(ft_comb_all)
        }

        for k, v in result_outputs.items():
            fltr_dict_all = [{'account_nm': an, 'fstype': ft} for an, ft in v['comb'].items()]
            fltr_dict_all = [{kk: vv for kk, vv in f.items() if vv != None} for f in fltr_dict_all]
            fltr_all = [[df[kk] == vv for kk, vv in fd.items()] for fd in fltr_dict_all]
            fltr_all = [reduce(lambda a, b: a & b, f) for f in fltr_all]
            fltr = reduce(lambda a, b: a | b, fltr_all)
            df_comb = df[fltr]
            del df_comb['fstype']
            indexes_comb = [c for c in df_comb.columns if c != 'value']
            df_comb = df_comb.set_index(indexes_comb).unstack('account_nm')
            cal_args = [df_comb[('value',c)] for c in self._arg_all]
            s = self._calculator(*cal_args)
            bybq_all = [[by,bq] for stock_code, by, bq in s.index.tolist()]
            result_outputs[k]['desc'] = {
                'n_stock': len(s.index.unique('stock_code')),
                'n_obs': len(s),
                'n_miss': int(s.isnull().sum()),
                'range_bybq': [f"{by}q{bq}" for by, bq in [min(bybq_all), max(bybq_all)]],
            }
        return {'result_inputs': result_inputs, 'result_outputs': result_outputs}


    def get_data(self):


# [{'account__accountNm': }]
# fltrs = [
#     {
#         'account__accountNm': 'CurrentAssets',
#         'fs__type__name': 'BS1',
#         'fs__corp__listedAt__isnull': False,
#     },
#     {
#         'account__accountNm': 'CurrentLiabilities',
#         'fs__type__name': 'BS1',
#         'fs__corp__listedAt__isnull': False,
#     },
# ]
#
# filters = {
#     'fs__type__name__in': ['BS1', 'BS2'],
#     'fs__corp__listedAt__isnull': False,
#     'account__accountNm__in': ['CurrentAssets','CurrentLiabilities'],
# }

# def set_label_kor(label_kor):
#     def decorator(f):
#         f.__dict__['label_kor'] = label_kor
#         return f
#     return decorator


        # # inspect account
        # for a in self._arg_all:
        #     if multiple_ft:
        #         if is_df_by_ft:
        #             pass
        #         else:
        #             pass
        #     else:
        #         pass


        # for an accountNm
        # if single fstype:
        # pass
        # - elif ~ = 1 : m
#         pass
#
#     def get_data(self, **kwargs):
#         pass
#
# class AccountRatio:
#     def __init__(self,name,label_kor,syntax):
#         self._name = name
#         self._label_kor = label_kor
#         self._syntax = syntax
#
# # # get recent version of account tree
# class AccountRatios:
#
#     def __init__(self):
#         self._name = 'account-ratios'
#         self._label_kor = '재무비율'
#         self._fsinfo = {
#             # 'fs__type__name': 'fsType',
#             'fs__by': 'by',
#             'fs__bq': 'bq',
#         }
#         self._corpinfo = {
#             'fs__corp__fye': 'fye',
#             'fs__corp__market': 'market',
#             'fs__corp__industry': 'industry',
#             'fs__corp__stockCode': 'stkCd',
#             'fs__corp__corpName': 'corpNm',
#         }
#         self._common_fields = list(self._fsinfo.keys()) + ['account__accountNm', 'value']
#
#
#     @set_label_kor('유동비율')
#     def ca2cl(self, **kwargs):
#
#         # (step1) set inputs to query data
#         all = kwargs.pop('all','')
#
#         # filters, filters and indices
#         fields = self._common_fields
#         if all == True:
#             fields = fields + list(self._corpinfo.keys())
#         else:
#             stockCode = kwargs.pop('stockCode','')
#             filters['fs__corp__stockCode'] = stockCode
#
#         indices = [f for f in fields if f != 'value']
#
#         # (step2) query data
#         t0 = time.time()
#
#         qs = (
#             F
#         )
#         df = query_df_fd(filters=filters, fields=fields, indices=indices)
#         t1 = time.time()
#         print(f"query data as df: {t1-t0}")
#         # df = df.unstack('account__accountNm')
#
#         # (step3) get value
#         s = (df[('value','CurrentAssets')]/df[('value','CurrentLiabilities')])
#         t2 = time.time()
#         print(f"get value: {t2-t1}")
#
#         # return s
#         # (step4) rearrange data to display
#         is_one2many = 0 in s.unstack('fs__type__name').isnull().astype(int).sum(axis=1).unique()
#         rename_map = {**self._fsinfo, **self._corpinfo}
#         if is_one2many:
#             uniq_ft = s.index.get_level_values('fs__type__name').unique()
#             return {f"result-{ft}": s2table_data(s[ft],ascending=False,rename_map=rename_map) for ft in uniq_ft}
#         else:
#             return {'result': s2table_data(s, ascending=False, rename_map=rename_map)}
#
#
#     @set_label_kor('부채비율')
#     def l2eatoop(self, **kwargs):
#
#         # (step1) set inputs to query data
#         all = kwargs.pop('all','')
#
#         # filters, filters and indices
#         filters = {
#             'fs__type__name__in': ['BS1', 'BS3'],
#             'fs__corp__listedAt__isnull': False,
#             'account__accountNm__in': ['Liabilities','EquityAttributableToOwnersOfParent'],
#         }
#         fields = self._common_fields
#         if all == True:
#             fields = fields + list(self._corpinfo.keys())
#         else:
#             stockCode = kwargs.pop('stockCode','')
#             filters['fs__corp__stockCode'] = stockCode
#
#         indices = [f for f in fields if f != 'value']
#
#         # (step2) query data
#         t0 = time.time()
#         df = query_df_fd(filters=filters, fields=fields, indices=indices)
#         t1 = time.time()
#         print(f"query data as df: {t1-t0}")
#         # df = df.unstack('account__accountNm')
#
#         # (step3) get value
#         s = (df[('value','Liabilities')]/df[('value','EquityAttributableToOwnersOfParent')])
#         t2 = time.time()
#         print(f"get value: {t2-t1}")
#
#         # (step4) rearrange data to display
#         # is_one2many = 0 in s.unstack('fsType').isnull().astype(int).sum(axis=1).unique()
#         # if is_one2many:
#         rename_map = {**self._fsinfo, **self._corpinfo}
#         return s.rename('value')#.reset_index().rename(columns=rename_map).set_index(indices)
#
#
#     # @set_label_kor('부채비율')
#     # def l2eatoop(self, **kwargs):
#     #     all = kwargs.pop('all','')
#     #
#     #     fields = (
#     #         list(self._fsinfo.keys())
#     #         + ['account__accountNm', 'value']
#     #     )
#     #
#     #     if all == True:
#     #         fields = fields + list(self._corpinfo.keys())
#     #     else:
#     #         stockCode = kwargs.pop('stockCode','')
#     #         filters['fs__corp__stockCode'] = stockCode
#     #
#     #     indices = [f for f in fields if f != 'value']
#     #     df = query_df_fd(filters=filters, fields=fields, indices=indices)
#     #     # df = df.unstack('account__accountNm')
#     #
#     #     rename_map = {**self._fsinfo, **self._corpinfo}
#     #     return s.rename('value').reset_index().rename(columns=rename_map)
#
#
#     # @set_label_kor('부채비율')
#     # def tl2eo(self, **kwargs):
#     #     all = kwargs.pop('all','')
#     #     fields = [
#     #         'fs__by', 'fs__bq', 'fs__type__name',
#     #         'account__accountNm', 'value',
#     #     ]
#     #     if all == True:
#     #         fields = ['fs__corp__stockCode', 'fs__corp__corpName'] + fields
#     #     else:
#     #         stockCode = kwargs.pop('stockCode','')
#     #         filters['fs__corp__stockCode'] = stockCode
#     #
#     #     indices = fields[:-1]
#     #     df = query_df_fd(filters=filters, fields=fields, indices=indices)
#     #     df = df.unstack('account__accountNm')
#     #     s = (df[('value','Liabilities')]/df[('value','EquityAttributableToOwnersOfParent')])#.unstack('fs__type__name')
#     #     rename_map = {
#     #         'fs__corp__stockCode': 'stkCd',
#     #         'fs__corp__corpName': 'corpNm',
#     #         'fs__type__name': 'fsType',
#     #         'fs__by': 'by',
#     #         'fs__bq': 'bq',
#     #     }
#     #     return s.rename('value').reset_index().rename(columns=rename_map).to_dict(orient='records')
#
#
#
# def get_ar_elements(**kwargs):
#     qs = (
#         FsDetail.objects
#         .select_related('fs','fs__corp','fs__type','account')
#         .filter(**filters)
#     ).order_by('fs__id','account__id')
#     return
#
#
# def query_df_fd(**kwargs):
#     t0 = time.time()
#     qs = (
#         FsDetail.objects.filter(**kwargs['filters'])
#         .select_related('fs','fs__corp','fs__type','account')
#     )
#     t1 = time.time()
#     print(f"{t1-t0} sec for django query")
#     df = pd.DataFrame.from_records(qs.values(*kwargs['fields']))
#     t2 = time.time()
#     print(f"{t2-t1} sec to convert django queryset to pd df")
#     df = df.drop_duplicates(kwargs['indices']).set_index(kwargs['indices']).unstack('account__accountNm')
#     t3 = time.time()
#     print(f"{t3-t2} sec to beautifulize df")
#     # df = df.sort_values(['fs__by','fs__bq'],ascending=[False,False])
#     return df
#     # return df.drop_duplicates(kwargs['indices']).set_index(kwargs['indices']).unstack('account__accountNm')
#
#
# def s2table_data(s,**kwargs):
#     ascending = kwargs.pop('ascending')
#     rename_map = kwargs.pop('rename_map')
#     s = s.unstack(['fs__by','fs__bq']).round(2)
#     colord = s.columns.sortlevel(ascending=False)[0]
#     latest = colord[0]
#     s = s[colord].sort_values(latest,ascending=ascending)
#     s.columns = [f"{x[0]}q{x[1]}" for x in s.columns]
#     df = s.replace({np.nan:None,np.inf:None}).reset_index().rename(columns=rename_map)
#     return {
#         'header': df.columns.tolist(),
#         'rows': df.values.tolist(),
#     }
#
# def is_one2many(s)
# def reshape_s(s):
#     s.rename('value')
