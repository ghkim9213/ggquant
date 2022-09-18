from django.db import models
from ggdb.models import Corp
from ggdb.models import FsAccountLite
from ggdb.models import FsDetail

import pandas as pd

# Create your models here.

## models

class WebsocketClient(models.Model):
    channel_name = models.CharField(max_length=256)



## model-likes

class FaTimeSeries(models.Model):
    fa = models.ForeignKey(
        FsAccountLite,
        related_name = 'ts',
        on_delete = models.CASCADE,
    )
    corp = models.ForeignKey(
        Corp,
        related_name = 'fa_ts',
        on_delete = models.CASCADE,
    )

    class Meta:
        db_table = 'fa_ts'

    @property
    def obs(self):
        # corp = Corp.objects.get(stockCode=self.stock_code)
        fltr = {
            'account__accountNm': self.fa.name,
            'fs__corp': self.corp,
            'fs__type__oc': self.fa.oc,
        }
        FIELDS = {
            'fs__fqe': 'fqe',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'fs__type__name': 'ft',
            'value': 'value'
        }
        # query
        qs = (
            FsDetail.objects
            .filter(**fltr)
            .select_related('fs','fs__type')
        )
        if not qs.exists():
            return pd.DataFrame()

        ft_div = qs.first().fs.type.type

        # clean data
        df = pd.DataFrame.from_records(qs.values(*FIELDS.keys())).rename(columns=FIELDS)
        df.fqe = pd.to_datetime(df.fqe)

        # dups in PL
        if ft_div == 'PL':
            ft_prefix_uniq = df.ft.str[:-1].unique()
            if ('IS' in ft_prefix_uniq) and ('CIS' in ft_prefix_uniq):
                df = df.loc[df.ft.str[:-1] != 'CIS']

        # keep representitive values only
        ft_count = df.ft.value_counts().to_dict()
        df['ft_order'] = df.ft.replace(ft_count)
        df = df.sort_values(
            ['fqe', 'ft_order'],
            ascending = [False, False]
        ).drop_duplicates('fqe')
        del df['ft_order']

        if ft_div == 'BS':
            return df.sort_values('fqe')[['fqe', 'value']]
        else:
            # fix by bq
            df = df.sort_values('fqe')
            mgap = df.fqe.dt.month - self.corp.fye
            ydiff =  -((mgap <= 0) & (self.corp.fye != 12)).astype(int)
            df.by = df.fqe.dt.year + ydiff
            df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

            idx2fqe = (
                df[['by','bq','fqe']]
                .set_index(['by','bq'])
                .fqe.to_dict()
            )
            dfq = (
                df[['by','bq','value']]
                .set_index(['by','bq'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1]+dfq[2]+dfq[3])
            dfq = dfq.stack().rename('value').to_frame()
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            return dfq.reset_index()[['fqe','value']]

# class FaTimeSeries:
#     def __init__(self, acnt_nm, oc, stock_code):
#         self.acnt_nm = acnt_nm
#         self.oc = oc
#         self.stock_code = stock_code
#
#     @property
#     def obs(self):
#         corp = Corp.objects.get(stockCode=self.stock_code)
#         fltr = {
#             'account__accountNm': self.acnt_nm,
#             'fs__corp': corp,
#             'fs__type__oc': self.oc,
#         }
#         FIELDS = {
#             'fs__fqe': 'fqe',
#             'fs__by': 'by',
#             'fs__bq': 'bq',
#             'fs__type__name': 'ft',
#             'value': 'value'
#         }
#         # query
#         qs = (
#             FsDetail.objects
#             .filter(**fltr)
#             .select_related('fs','fs__type')
#         )
#         if not qs.exists():
#             return pd.DataFrame()
#
#         ft_div = qs.first().fs.type.type
#
#         # clean data
#         df = pd.DataFrame.from_records(qs.values(*FIELDS.keys())).rename(columns=FIELDS)
#         df.fqe = pd.to_datetime(df.fqe)
#
#         # dups in PL
#         if ft_div == 'PL':
#             ft_prefix_uniq = df.ft.str[:-1].unique()
#             if ('IS' in ft_prefix_uniq) and ('CIS' in ft_prefix_uniq):
#                 df = df.loc[df.ft.str[:-1] != 'CIS']
#
#         # keep representitive values only
#         ft_count = df.ft.value_counts().to_dict()
#         df['ft_order'] = df.ft.replace(ft_count)
#         df = df.sort_values(
#             ['fqe', 'ft_order'],
#             ascending = [False, False]
#         ).drop_duplicates('fqe')
#         del df['ft_order']
#
#         if ft_div == 'BS':
#             return df.sort_values('fqe')[['fqe', 'value']]
#         else:
#             # fix by bq
#             df = df.sort_values('fqe')
#             mgap = df.fqe.dt.month - corp.fye
#             ydiff =  -((mgap <= 0) & (corp.fye != 12)).astype(int)
#             df.by = df.fqe.dt.year + ydiff
#             df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3
#
#             idx2fqe = (
#                 df[['by','bq','fqe']]
#                 .set_index(['by','bq'])
#                 .fqe.to_dict()
#             )
#             dfq = (
#                 df[['by','bq','value']]
#                 .set_index(['by','bq'])
#                 .value.unstack('bq')
#             )
#             dfq[4] = dfq[4] - (dfq[1]+dfq[2]+dfq[3])
#             dfq = dfq.stack().rename('value').to_frame()
#             dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
#             return dfq.reset_index()[['fqe','value']]


## many-to-many mapping models



# FaCrossSection is devised for faster handling FaSeries
# , a class of data series for a financial account.
# Because of complexity in relationships among models,
# it takes so long time to directly query data from FsDetail
# , which is a model for values of financial accounts.
# This helps to save time to query using predefined shortcut keys ('source' field)
# Using this, it takes to xx sec while the direct query does 5 ~ 10 secs.


class FaCrossSection(models.Model):
    fa = models.ForeignKey(
        FsAccountLite,
        related_name = 'cs',
        on_delete = models.CASCADE,
    )
    market = models.CharField(max_length=6)
    tp = models.DateField()
    source = models.ManyToManyField(FsDetail)
    updatedAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'fa_cs'

    @property
    def obs(self):
        FIELDS = {
            'fs__corp__stockCode': 'stock_code',
            'fs__corp__corpName': 'corp_name',
            'fs__corp__fye': 'fye',
            'fs__fqe': 'fqe',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'value': 'value'
        }
        ft_div = self.source.first().fs.type.type
        df = pd.DataFrame.from_records(self.source.values(*FIELDS.keys())).rename(columns=FIELDS)
        df.fqe = pd.to_datetime(df.fqe)
        # if ft_div == 'BS':
        #     return df[['stock_code', 'corp_name', 'fqe', 'value']]
        if ft_div != 'BS':
            df = df.sort_values(['stock_code','fqe'])
            mgap = df.fqe.dt.month - df.fye
            ydiff =  -((mgap <= 0) & (df.fye != 12)).astype(int)
            df.by = df.fqe.dt.year + ydiff
            df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

            idx2fqe = (
                df[['stock_code','corp_name','by','bq','fqe']]
                .set_index(['stock_code', 'corp_name','by','bq'])
                .fqe.to_dict()
            )
            dfq = (
                df[['stock_code','corp_name','by','bq','value']]
                .set_index(['stock_code','corp_name','by','bq'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1] + dfq[2] + dfq[3])
            dfq = dfq.stack().rename('value').to_frame()
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            df = dfq.reset_index()[['stock_code','corp_name','fqe','value']]
        df = df.sort_values(
            ['stock_code','fqe'],
            ascending = [True, False]
        ).drop_duplicates('stock_code')
        valid = self.tp - df.fqe.dt.date <= '62 days'
        return df.loc[valid].reset_index(drop=True)


# class FaCrossSection(models.Model):
#     name = models.CharField(max_length=256)
#     oc = models.CharField(max_length=3)
#     market = models.CharField(max_length=6)
#     tp = models.DateField()
#     source = models.ManyToManyField(FsDetail)
#     updatedAt = models.DateField(auto_now_add=True)
#
#     class Meta:
#         db_table = 'fa_cs'
#
#     @property
#     def obs(self):
#         FIELDS = {
#             'fs__corp__stockCode': 'stock_code',
#             'fs__corp__corpName': 'corp_name',
#             'fs__corp__fye': 'fye',
#             'fs__fqe': 'fqe',
#             'fs__by': 'by',
#             'fs__bq': 'bq',
#             'value': 'value'
#         }
#         ft_div = self.source.first().fs.type.type
#         df = pd.DataFrame.from_records(self.source.values(*FIELDS.keys())).rename(columns=FIELDS)
#         df.fqe = pd.to_datetime(df.fqe)
#         # if ft_div == 'BS':
#         #     return df[['stock_code', 'corp_name', 'fqe', 'value']]
#         if ft_div != 'BS':
#             df = df.sort_values(['stock_code','fqe'])
#             mgap = df.fqe.dt.month - df.fye
#             ydiff =  -((mgap <= 0) & (df.fye != 12)).astype(int)
#             df.by = df.fqe.dt.year + ydiff
#             df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3
#
#             idx2fqe = (
#                 df[['stock_code','corp_name','by','bq','fqe']]
#                 .set_index(['stock_code', 'corp_name','by','bq'])
#                 .fqe.to_dict()
#             )
#             dfq = (
#                 df[['stock_code','corp_name','by','bq','value']]
#                 .set_index(['stock_code','corp_name','by','bq'])
#                 .value.unstack('bq')
#             )
#             dfq[4] = dfq[4] - (dfq[1] + dfq[2] + dfq[3])
#             dfq = dfq.stack().rename('value').to_frame()
#             dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
#             df = dfq.reset_index()[['stock_code','corp_name','fqe','value']]
#         df = df.sort_values(
#             ['stock_code','fqe'],
#             ascending = [True, False]
#         ).drop_duplicates('stock_code')
#         valid = self.tp - df.fqe.dt.date <= '62 days'
#         return df.loc[valid].reset_index(drop=True)
