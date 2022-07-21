from collections import Counter
from django.db import models
from dashboard.data_visualizers import *
from functools import reduce

import numpy as np
import pandas as pd
import itertools, json, re
# Create your models here.

class Corp(models.Model):
    stockCode = models.CharField(max_length=6,blank=False,null=False,unique=True)
    corpCode = models.CharField(max_length=8,blank=True,null=True)
    # corpCode = models.CharField(max_length=8,blank=False,null=False)
    # stockCode = models.CharField(max_length=6,blank=True,null=True)
    corpName = models.CharField(max_length=128,blank=False,null=False)
    industry = models.CharField(max_length=128,blank=True,null=True)
    product = models.CharField(max_length=128,blank=True,null=True)
    ceo = models.CharField(max_length=128,blank=True,null=True)
    homepage = models.CharField(max_length=128,blank=True,null=True)
    district = models.CharField(max_length=128,blank=True,null=True)
    market = models.CharField(max_length=6,blank=True,null=True)
    fye = models.IntegerField(blank=True,null=True)
    listedAt = models.DateField(blank=True,null=True)
    delistedAt = models.DateField(blank=True,null=True)

    class Meta:
        db_table = 'corp'
        ordering = ['-listedAt']
        indexes = [
            models.Index(fields=['stockCode','corpCode','industry','listedAt'])
        ]



class CorpHistory(models.Model):
    corp = models.ForeignKey(
        Corp,
        related_name = 'history',
        on_delete = models.CASCADE,
    )
    changeIn = models.CharField(max_length=16)
    prevValue = models.CharField(max_length=128)
    updatedAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'corp_history'
        get_latest_by = 'updatedAt'



class Tick(models.Model):
    corp = models.ForeignKey(
        Corp,
        related_name = 'ticks',
        on_delete = models.CASCADE,
    )
    datetime = models.DateTimeField()
    market = models.CharField(max_length=6)
    price = models.IntegerField()
    side = models.CharField(max_length=1)
    volume = models.IntegerField()

    class Meta:
        get_latest_by = 'id'
        db_table = 'tick'


class Minute(models.Model):
    corp = models.ForeignKey(
        Corp,
        related_name = 'minutes',
        on_delete = models.CASCADE,
    )
    datetime = models.DateTimeField()
    market = models.CharField(max_length=6)
    open = models.IntegerField()
    high = models.IntegerField()
    low = models.IntegerField()
    close = models.IntegerField()
    volume = models.IntegerField()
    volume_m = models.IntegerField()

    class Meta:
        get_latest_by = 'datetime'
        db_table = 'minute'


# Models for financial statments

fsversion_all = ['20130331','20171001','20180720','20191028']


class FsType(models.Model):
    name = models.CharField(max_length=8)
    # version = models.DateField(blank=True,null=True)
    type = models.CharField(max_length=8)
    method = models.CharField(max_length=32)
    oc = models.CharField(max_length=3)

    class Meta:
        db_table = 'fstype'
        get_latest_by = 'version'
        indexes = [
            models.Index(fields=['name'])
        ]




class Fs(models.Model):
    corp = models.ForeignKey(
        Corp,
        related_name = 'fs',
        on_delete = models.CASCADE,
    )
    by = models.IntegerField()
    bq = models.IntegerField()
    rptDate = models.DateField()
    type = models.ForeignKey(
        FsType,
        related_name = 'articles',
        on_delete = models.CASCADE,
    )

    class Meta:
        db_table = 'fs'
        indexes = [
            models.Index(fields=['corp','type','by','bq']),
        ]



class FsAccount(models.Model):
    type = models.ForeignKey(
        FsType,
        related_name = 'accounts',
        on_delete = models.CASCADE,
    )
    accountNm = models.CharField(max_length=256,blank=True,null=True)
    accountId = models.CharField(max_length=256)
    version = models.DateField(blank=True,null=True)
    isStandard = models.BooleanField(default=True)
    parent = models.ForeignKey(
        'self',
        related_name = 'childs',
        on_delete = models.CASCADE,
        blank = True, null = True,
    )
    matchedWith = models.ForeignKey(
        'self',
        related_name = 'nstd_siblings',
        on_delete = models.CASCADE,
        blank = True, null = True,
    )
    labelEng = models.CharField(max_length=256,null=True,blank=True)
    labelKor = models.CharField(max_length=256)

    class Meta:
        get_latest_by = 'version'
        db_table = 'fsaccount'
        indexes = [
            models.Index(fields=['accountNm','accountId','type','version'])
        ]


class FsDetail(models.Model):
    fs = models.ForeignKey(
        Fs,
        related_name = 'details',
        on_delete = models.CASCADE,
    )
    account = models.ForeignKey( # rename 'account'
        FsAccount,
        related_name = 'values',
        on_delete = models.CASCADE,
    )
    value = models.BigIntegerField(null=True,blank=True)
    createdAt = models.DateField(auto_now_add=True)
    currency = models.CharField(max_length=8,null=True,blank=True)

    class Meta:
        db_table = 'fsdetail'
        get_latest_by = 'createdAt'
        indexes = [
            models.Index(fields=['account','fs']),
        ]


class AccountRatio(models.Model):
    name = models.CharField(max_length=32)
    div = models.CharField(max_length=32)
    labelKor = models.CharField(max_length=128)
    syntax = models.CharField(max_length=256)
    changeIn = models.BooleanField(default=False)
    inspectInputs = models.JSONField(null=True,blank=True)

    class Meta:
        db_table = 'account_ratio'

    @property
    def arg_all(self):
        return re.findall('`(.*?)`', self.syntax)

    @property
    def syntax_katex(self):
        syntax_katex = self.syntax
        labelKor_all = [FsAccount.objects.filter(accountNm=arg).last().labelKor for arg in self.arg_all]
        for k, v in dict(zip(self.arg_all,labelKor_all)).items():
            syntax_katex = syntax_katex.replace(k,f"\\text{{{v}}}")
        syntax_katex = syntax_katex.replace('*','\times').replace("`","")
        return f"\\text{{{self.labelKor}}}={syntax_katex}"

    @property
    def operation(self):
        strargs = str(self.arg_all)[1:-1].replace("'","")
        strfunc = f"lambda {strargs}:" + self.syntax.replace("`","")
        return eval(strfunc)

    @property
    def default_fields(self):
        return {
            # 'fs__corp__market': 'market',
            'fs__corp__stockCode': 'stock_code',
            # 'fs__corp__corpName': 'corp_name',
            'fs__by': 'by',
            'fs__bq': 'bq',
            # 'account__accountNm': 'acnt_nm',
            # 'value': 'value',
        }

    @property
    def default_fltr(self):
        return {
            'fs__corp__listedAt__isnull' : False,
        }

    def inspect_inputs(self, **kwargs) -> dict:
        ft_div_lk_map = {
            'BS': '재무상태표',
            'CF': '현금흐름표',
            'IS': '(포괄)손익계산서'
        }
        fields_inspct = {
            **self.default_fields,
            'fs__type__type':'ft_div',
            'fs__type__name': 'fstype',
            'id': 'fd_id'
        }
        inspect_inputs = {}
        for acnt_nm in self.arg_all:
            fltr_a = {**self.default_fltr, 'account__accountNm': acnt_nm}
            acnt_in = (
                FsDetail.objects
                .select_related('fs','fs__corp','fs__type','account')
                .filter(**fltr_a)
                .values(*fields_inspct)
            )
            dfa = pd.DataFrame.from_records(acnt_in).rename(columns=fields_inspct)
            if len(dfa['ft_div'].unique()) == 1:
                ft_div = dfa['ft_div'].unique()[0]
                del dfa['ft_div']
            else:
                raise ValueError
            idcols = ['stock_code','by','bq','fstype']
            dfa = dfa.drop_duplicates(idcols)
            dfa_ft = dfa.groupby(['stock_code','by','bq']).fstype.value_counts().unstack().fillna(0)
            ft_ddiv_all = [c[:-1] for c in dfa_ft.columns]
            if ('IS' in ft_ddiv_all) and ('CIS' in ft_ddiv_all):
                dfa_ft = dfa_ft[[c for c in dfa_ft.columns if not c.startswith('CIS')]]
            ofscols = [c for c in dfa_ft.columns if int(c[-1:]) % 2 == 0]
            cfscols = [c for c in dfa_ft.columns if c not in ofscols]
            get_locs = lambda tgcols: dfa_ft[tgcols].loc[dfa_ft[tgcols].sum(axis=1)==1].stack().replace(0,np.nan).dropna().index
            get_dup_locs = lambda tgcols: dfa_ft[tgcols].loc[dfa_ft[tgcols].sum(axis=1)>1].stack().index
            fd_id = dfa.set_index(idcols).fd_id

            choice_all = {}
            for oc, cols in zip(['ofs','cfs'],[ofscols,cfscols]):
                s = fd_id.loc[get_locs(cols)]
                if len(s) > 0:
                    bybq_uniq = (s.index.get_level_values('by').astype(str) + 'q' + s.index.get_level_values('bq').astype(str)).unique()
                    stock_uniq = s.index.get_level_values('stock_code').unique()
                    choice_all[oc] = {
                        'label_kor': f"별도 {ft_div_lk_map[ft_div]}" if oc == 'ofs' else f"연결 {ft_div_lk_map[ft_div]}",
                        'bybq_range': [bybq_uniq.min(),bybq_uniq.max()],
                        'n_stock': len(stock_uniq),
                        'n_obs': len(s),
                        'fd_series': s.tolist()
                    }

            inspect_inputs[acnt_nm] = {
                'label_kor': FsAccount.objects.filter(accountNm=acnt_nm, isStandard=True).latest().labelKor,
                'choices': choice_all,
            }
            # inspect_inputs.append({
            #     'name': acnt_nm,
            # })
        return inspect_inputs


    def get_data(self, selected_inpt_all, selected_series_all, **kwargs):
        # setting inputs for query
        stock_code = kwargs.pop('stockCode', None)
        fd_id_all = reduce(
            lambda a, b: a+b,
            [
                self.inspectInputs[nm]['choices'][oc]['fd_series']
                for nm, oc in zip(selected_inpt_all, selected_series_all)
            ]
        )
        qs_fltr = {**self.default_fltr, 'id__in': sorted(fd_id_all)}
        if stock_code != None:
            qs_fltr['fs__corp__stockCode'] = stock_code

        fields = {
            **self.default_fields,
            'fs__corp__market': 'market',
            'fs__corp__corpName': 'corp_name',
            'account__accountNm': 'acnt_nm',
            'value': 'value',
        }

        # query
        qs = (
            FsDetail.objects
            .select_related('fs','fs__corp','account')
            .filter(**qs_fltr)
        )

        # queryset to dataframe
        df = (
            pd.DataFrame
            .from_records(qs.values(*fields.keys()))
            .rename(columns=fields)
        )
        # colord = ['market', '']

        # calculate the values
        id = [c for c in df.columns if c !='value']
        # return df
        # value
        df=df.drop_duplicates(id).set_index(id).unstack('acnt_nm')
        cal_args = [df[('value'),c] for c in self.arg_all]
        s = self.operation(*cal_args).dropna().rename('value')
        id_s = list(s.index.names)
        order_by = ['stock_code','by','bq']
        value_all = s.reset_index().sort_values(order_by, ascending=[True,False,False]).set_index(id_s).unstack(['by','bq'])
        value_all.columns = [f"{c[1]}q{c[2]}" for c in value_all.columns] # flatten columns

        # ranking by recent values
        recent = value_all.apply(pd.Series.first_valid_index,axis=1).rename('recent')
        recent_value = pd.Series(
            [value_all[v][k] for k, v in recent.to_dict().items()]
            , index=recent.index).rename('recent_value')
        recent_rank = recent_value.rank(method='max', ascending=False).astype(int).rename('rank')
        recent_rank_pct = recent_value.rank(method='max', ascending=False,pct=True).rename('pct')

        return pd.concat([
            recent_rank,
            recent_rank_pct * 100,
            recent,
            recent_value,
            value_all
        ],axis=1).sort_values('rank')#.reset_index()



def get_series_label_kor(ftnm):
    ft = FsType.objects.get(name=ftnm)
    if ftnm[:-1] == 'BS':
        tnm = '재무상태표'
    elif ftnm[:-1] == 'IS':
        tnm = '손익계산서'
    elif ftnm[:-1] == 'CIS':
        tnm = '포괄손익계산서'
    elif ftnm[:-1] == 'DCIS':
        tnm = '단일 포괄손익계산서'
    elif ftnm[:-1] == 'CF':
        tnm = '현금흐름표'

    if ft.oc == 'OFS':
        oc = '별도'
    elif ft.oc == 'CFS':
        oc = '연결'
    return f"{tnm} ({oc}, {ft.method})"
