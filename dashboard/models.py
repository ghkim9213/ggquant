from django.db import models
from django.db.models import Value
from django.db.models.functions import Trim
from django.forms.models import model_to_dict
from functools import reduce
from ggdb.models import Corp
from ggdb.models import FsAccount
from ggdb.models import FsAccountLite
from ggdb.models import FsDetail

import datetime
import re
import pandas as pd

# Create your models here.

## models

class WebsocketClient(models.Model):
    channel_name = models.CharField(max_length=256)


class FaRoot(models.Model):
    fa = models.OneToOneField(
        FsAccount,
        on_delete = models.CASCADE,
    )
    stdVal = models.ManyToManyField(FsDetail, related_name='faroot_std')
    nstdVal = models.ManyToManyField(FsDetail, related_name='faroot_nstd')

    class Meta:
        db_table = 'fa_root'

    # json-serializable dict
    @property
    def info(self):
        return {
            'model': 'root',
            'id': self.id,
            'ft_div': self.fa.type.type,
            'ft_nm': self.fa.type.name,
            'ft_oc': self.fa.type.oc,
            'ft_method': self.fa.type.method,
            'fa_nm': self.fa.accountNm,
            'fa_lk': self.fa.labelKor,
        }

    @property
    def related_fa_all(self):
        return FsAccount.objects.filter(
            type__type = self.fa.type.type,
            accountNm = self.fa.accountNm,
        )

    @property
    def related_lk_all(self):
        related_std_all = reduce(
            lambda a, b: a | b, [
                fa.values
                .annotate(lk = Trim('labelKor'))
                for fa in self.related_fa_all
            ]
        )
        return (
            related_std_all
            .values_list('lk', flat=True)
            .distinct()
        )


class FaItem(models.Model):
    nm = models.CharField(max_length=256)
    lk = models.CharField(max_length=256)
    oc = models.CharField(max_length=3)
    root = models.ManyToManyField(FaRoot)

    class Meta:
        db_table = 'fa_item'

    # to json serializable dict
    @property
    def info(self):
        d = model_to_dict(self)
        d['model'] = 'item'
        root_all = d.pop('root')
        d['root'] = [r.info for r in root_all]
        return d

    def get_ts(self, stock_code, include_nstd=True):
        TS_FIELDS = {
            'fs__corp__fye': 'fye',
            'fs__fqe': 'fqe',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'is_std': 'is_std',
            'createdAt': 'created_at',
            'value': 'value'
        }

        corp = Corp.objects.get(stockCode=stock_code)
        root_all = self.root.all()
        ft_div = root_all.first().fa.type.type
        df_all = []
        for root in root_all:
            qs_std = (
                root.stdVal
                .select_related('fs__corp')
                .filter(fs__corp_id=corp.id)
                .annotate(is_std = Value(True))
            )
            if qs_std.exists():
                df_std = pd.DataFrame.from_records(
                    qs_std.values(*TS_FIELDS.keys())
                ).rename(columns = TS_FIELDS)
                df_all.append(df_std)
            if include_nstd:
                qs_nstd = (
                    root.nstdVal
                    .select_related('fs__corp')
                    .filter(fs__corp_id=corp.id)
                    .annotate(is_std = Value(False))
                )
                if qs_nstd.exists():
                    df_nstd = pd.DataFrame.from_records(
                        qs_nstd.values(*TS_FIELDS.keys())
                    ).rename(columns = TS_FIELDS)
                    df_all.append(df_nstd)
        if len(df_all) == 0:
            return pd.DataFrame()

        df = pd.concat(df_all, axis=0)
        df.fqe = pd.to_datetime(df.fqe)
        df = df.sort_values(
            ['fqe', 'created_at', 'is_std'],
            ascending = [False, False, False]
        ).drop_duplicates('fqe')

        if ft_div == 'BS':
            return df.sort_values('fqe')[['fqe', 'value', 'is_std']]
        else:
            # fix by bq
            df = df.sort_values('fqe')
            mgap = df.fqe.dt.month - corp.fye
            ydiff =  -((mgap <= 0) & (corp.fye != 12)).astype(int)
            df.by = df.fqe.dt.year + ydiff
            df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

            idx2fqe = (
                df[['by','bq','is_std','fqe']]
                .set_index(['by','bq','is_std'])
                .fqe.to_dict()
            )
            dfq = (
                df[['by','bq','is_std','value']]
                .set_index(['by','bq','is_std'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1]+dfq[2]+dfq[3])
            dfq = dfq.stack().rename('value').reset_index()
            dfq = dfq.set_index(['by', 'bq', 'is_std'])
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            return dfq.reset_index()[['fqe','value', 'is_std']]

    def get_cs(self, mkt, tp, include_nstd=True):
        CS_FIELDS = {
            'fs__corp__stockCode': 'stock_code',
            'fs__corp__corpName': 'corp_name',
            'fs__corp__fye': 'fye',
            'fs__fqe': 'fqe',
            'fs__type__name': 'ft',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'is_std': 'is_std',
            'createdAt': 'created_at',
            'value': 'value'
        }

        fqe_lte = tp
        fqe_gte = str(tp.year-1)+str(tp.month).zfill(2)+str(tp.day).zfill(2)
        fqe_gte = datetime.datetime.strptime(fqe_gte, '%Y%m%d').date()

        df_all = []
        root_all = self.root.all()
        ft_div = root_all.first().fa.type.type
        for root in root_all:
            qs_std = (
                root.stdVal
                .select_related('fs', 'fs__corp')
                .filter(
                    fs__corp__market = mkt,
                    fs__fqe__gte = fqe_gte,
                    fs__fqe__lte = fqe_lte,
                )
                .annotate(is_std=Value(True))
            )
            df_std = pd.DataFrame.from_records(
                qs_std.values(*CS_FIELDS.keys())
            ).rename(columns=CS_FIELDS)
            df_all.append(df_std)
            if include_nstd:
                qs_nstd = (
                    root.nstdVal
                    .select_related('fs', 'fs__corp')
                    .filter(
                        fs__fqe__gte = fqe_gte,
                        fs__fqe__lte = fqe_lte,
                    )
                    .annotate(is_std=Value(False))
                )
                df_nstd = pd.DataFrame.from_records(
                    qs_nstd.values(*CS_FIELDS.keys())
                ).rename(columns=CS_FIELDS)
                df_all.append(df_nstd)

        df = pd.concat(df_all, axis=0)
        df.fqe = pd.to_datetime(df.fqe)
        df = df.sort_values([
            'stock_code', 'fqe', 'is_std',
            'created_at', 'value'
        ])
        df = df.drop_duplicates(['stock_code', 'fqe'])
        if ft_div != 'BS':
            df = df.sort_values(['stock_code','fqe'])
            mgap = df.fqe.dt.month - df.fye
            ydiff =  -((mgap <= 0) & (df.fye != 12)).astype(int)
            df.by = df.fqe.dt.year + ydiff
            df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

            idx2fqe = (
                df[['stock_code','corp_name','by','bq','is_std','fqe']]
                .set_index(['stock_code', 'corp_name','by','is_std','bq'])
                .fqe.to_dict()
            )
            dfq = (
                df[['stock_code','corp_name','by','bq','is_std','value']]
                .set_index(['stock_code','corp_name','by','bq','is_std'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1] + dfq[2] + dfq[3])
            dfq = dfq.stack().rename('value').to_frame()
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            df = dfq.reset_index()[['stock_code','corp_name','fqe','is_std','value']]

        df = df.sort_values(
            ['stock_code','fqe'],
            ascending = [True, False]
        ).drop_duplicates('stock_code')
        valid = tp - df.fqe.dt.date <= '62 days'
        return df.loc[valid].reset_index(drop=True)


class FaProduct(models.Model):
    TYPE_CHOICES = [
        ('VALUE', '값'),
        ('RATIO', '비율'),
    ]
    DIV_CHOICES = [
        ('STAB', '안정성'),
        ('PROF', '수익성'),
        ('GROW', '성장성'),
        ('ACTV', '활동성'),
        ('PROD', '생산성'),
        ('ETC', '기타'),
    ]
    type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    div = models.CharField(max_length=4, choices=DIV_CHOICES, null=True)
    nm = models.CharField(max_length=256)
    abbrev = models.CharField(max_length=16, blank=True)
    lk = models.CharField(max_length=256)
    # oc = models.CharField(max_length=3)
    syntax = models.TextField()
    item = models.ManyToManyField(FaItem)
    item_self = models.ManyToManyField(
        'self',
        symmetrical = False,
        related_name = 'products',
    )

    class Meta:
        db_table = 'fa_product'

    @property
    def syntax_ordered_item_nm_set(self):
        ordered_item_all = re.findall('\[(.*?)\]', self.syntax)
        return list(set(ordered_item_all))

    @property
    def operator(self):
        stritem_set = str(self.syntax_ordered_item_nm_set)[1:-1].replace("'","")
        stroper = self.syntax.replace('[','').replace(']','')
        strfunc = f"lambda {stritem_set}: {stroper}"
        return eval(strfunc)

    @property
    def oc(self):
        item_all = self.item.all()
        item_self_all = self.item_self.all()
        oc_all = [i.oc for i in item_all|item_self_all]
        if all([oc == 'CFS' for oc in oc_all]):
            return 'CFS'
        elif all([oc == 'OFS' for oc in oc_all]):
            return 'OFS'
        else:
            return 'MIXED'

    @property
    def info(self):
        d = model_to_dict(self)
        d['model'] = 'product'
        item_all = d.pop('item')
        d['item'] = [i.info for i in item_all]
        item_self_all = d.pop('item_self')
        d['item_self'] = [i.info for i in item_self_all]
        return d

    def get_ts(self, stock_code, include_nstd=True):
        ts_all = []
        item_all = self.item.all()
        for i in item_all:
            colnm = f"{i.nm}_{i.oc}"
            ts = i.get_ts(stock_code, include_nstd=include_nstd)
            if len(ts) > 0:
                del ts['is_std']
                ts = ts.set_index('fqe').rename(columns={'value': colnm})
                ts_all.append(ts)
            else:
                return pd.DataFrame()
        df = pd.concat(ts_all, axis=1)
        s = self.operator(*[df[c] for c in self.syntax_ordered_item_nm_set])
        return s.rename('value').reset_index()

    def get_cs(self, mkt, tp, include_nstd=True):
        cs_all = []
        item_all = self.item.all()
        for i in item_all:
            colnm = f"{i.nm}_{i.oc}"
            cs = i.get_cs(mkt, tp, include_nstd=include_nstd)
            if len(cs) > 0:
                del cs['is_std']
                cs = (
                    cs.set_index(['stock_code', 'corp_name', 'fqe'])
                    .rename(columns={'value': colnm})
                )
                cs_all.append(cs)
            else:
                return pd.DataFrame()
        df = pd.concat(cs_all, axis=1)
        s = self.operator(*[df[c] for c in self.syntax_ordered_item_nm_set])
        return s.rename('value').reset_index()


    # def collect_ts(self, include_nstd):
    #     item_all = self.item.all()
    #     ts_all = [
    #         i.get_ts(include_nstd = include_nstd)
    #         for i in item_all
    #     ]
    #     if self.item_self.exists():
    #         return ts_all + [
    #             i.collect_ts(include_nstd)
    #             for i in self.item_self
    #         ]
    #     else:
    #         return ts_all


# class FaItemEtc(FaProduct):
#     class Meta:
#         db_table = 'fa_item_etc'

# class FaRatio(FaProduct):
#     # item_etc = models.ManyToManyField(FaItemEtc)
#     class Meta:
#         db_table = 'fa_ratio'

# class FaItemEtc(models.Model):
#     nm = models.CharField(max_length=256)
#     lk = models.CharField(max_length=256)
#     oc = models.CharField(max_length=3)
#     syntax = models.TextField()
#     item = models.ManyToManyField(FaItem)
#
#     class Meta:
#         db_table = 'fa_item_etc'
#
#
#     def get_ts(self, stock_code, include_nstd=True):
#         item_all = self.item.all()
#         ts_all = []
#         for item in item_all:
#             ts = item.get_ts(stock_code, include_nstd=include_nstd)

# class FaRatio(models.Model):
#     nm = models.CharField(max_length=256)
#     abbrev = models.CharField(max_length=32)
#     lk = models.CharField(max_length=256)
#     operation = models.CharField(max_length=256)
#     items = models.ManyToManyField(FsAccount)
#
#     class Meta:
#         db_table = 'fa_product'
#
#     def get_info(self):
#
#
#         pass
#
#     def inspect(self, to_json = True):
#         info = {
#             'oc': self.oc,
#             'nm': self.name,
#             'lk': self.lk,
#             'items': []
#         }
#         pass
#
#     def growth(self):
#         pass
#
#     def get_ts(self):
#         pass
#
#     def get_cs(self):
#         pass
#
#     def get_panel(self):
#         pass


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
        # std
        fltr_std = {
            'account__accountNm': self.fa.name,
            'fs__corp': self.corp,
            'fs__type__oc': self.fa.oc,
        }
        # nstd
        fltr_nstd = {
            'account': None,
            'matched__accountNm': self.fa.name,
            'fs__corp': self.corp,
            'fs__type__oc': self.fa.oc,
        }
        FIELDS = {
            'fs__fqe': 'fqe',
            'fs__by': 'by',
            'fs__bq': 'bq',
            'fs__type__name': 'ft',
            'is_std': 'is_std',
            'value': 'value',
            'createdAt': 'created_at',
        }
        # query
        qs_std = (
            FsDetail.objects
            .filter(**fltr_std)
            .annotate(is_std = Value(True))
            .select_related('fs','fs__type')
        )
        # print(qs_std.count())
        qs_nstd = (
            FsDetail.objects
            .filter(**fltr_nstd)
            .annotate(is_std = Value(False))
            .select_related('fs','fs__type')
        )
        # print(qs_nstd.count())
        qs = qs_std | qs_nstd
        if not (qs_std | qs_nstd).exists():
            return pd.DataFrame()
        else:
            ft_div = (qs_std | qs_nstd).first().fs.type.type

        # clean data
        df_std = pd.DataFrame.from_records(qs_std.values(*FIELDS.keys())).rename(columns=FIELDS)
        df_nstd = pd.DataFrame.from_records(qs_nstd.values(*FIELDS.keys())).rename(columns=FIELDS)
        df = pd.concat([df_std,df_nstd],axis=0)
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
            ['fqe', 'ft_order', 'created_at', 'is_std'],
            ascending = [False, False, False, False]
        ).drop_duplicates('fqe')

        if ft_div == 'BS':
            return df.sort_values('fqe')[['fqe', 'value', 'is_std']]
        else:
            # fix by bq
            df = df.sort_values('fqe')
            mgap = df.fqe.dt.month - self.corp.fye
            ydiff =  -((mgap <= 0) & (self.corp.fye != 12)).astype(int)
            df.by = df.fqe.dt.year + ydiff
            df.bq = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

            idx2fqe = (
                df[['by','bq','is_std','fqe']]
                .set_index(['by','bq','is_std'])
                .fqe.to_dict()
            )
            dfq = (
                df[['by','bq','is_std','value']]
                .set_index(['by','bq','is_std'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1]+dfq[2]+dfq[3])
            dfq = dfq.stack().rename('value').reset_index()
            dfq = dfq.set_index(['by', 'bq', 'is_std'])
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            return dfq.reset_index()[['fqe','value', 'is_std']]


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


class FaCsSourceNotRegisteredError(Exception):
    def __init__(self, fa):
        msg = f"Source for [{fa}, {mkt}, {tp}] not found."
        super.__init__(msg)

class FaCsSourceAlreadyExistsError(Exception):
    def __init__(self, fa):
        msg = f"Source for [{fa}, {mkt}, {tp}] already exists."
        super.__init__(msg)
