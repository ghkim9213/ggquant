from collections import Counter
from django.db import models
from dashboard.data_visualizers import *
from dashboard.modeltools import *
from functools import reduce

import numpy as np
import pandas as pd
import datetime, itertools, json, re
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

PREFIX_TO_LABKOR = {
    'BS': '재무상태표',
    'IS': '손익계산서',
    'CIS': '기타포괄손익계산서',
    'DCIS': '포괄손익계산서',
    'CF': '현금흐름표'
}

LABKOR_TO_PREFIX_MAP = {
    '재무상태표': 'BS',
    '손익계산서': 'IS',
    '포괄손익계산서(세후기타포괄손익)': 'CIS',
    '포괄손익계산서(세전기타포괄손익)': 'CIS',
    '포괄손익계산서': 'DCIS',
    '현금흐름표': 'CF',
}


class FsType(models.Model):
    name = models.CharField(max_length=8)
    type = models.CharField(max_length=8)
    method = models.CharField(max_length=32)
    oc = models.CharField(max_length=3)
    required = models.BooleanField(default=True)

    class Meta:
        db_table = 'fstype'
        indexes = [
            models.Index(fields=['name'])
        ]

    @property
    def labelKor(self):
        global PREFIX_TO_LABKOR
        oc_lk = '별도' if self.oc == 'OFS' else '연결'
        name_lk = PREFIX_TO_LABKOR[self.name[:-1]]
        return f"{oc_lk} {name_lk} ({self.method})"


class Fs(models.Model):
    corp = models.ForeignKey(
        Corp,
        related_name = 'fs',
        on_delete = models.CASCADE,
    )
    by = models.IntegerField()
    bq = models.IntegerField()
    fqe = models.DateField()
    type = models.ForeignKey(
        FsType,
        related_name = 'articles',
        on_delete = models.CASCADE,
    )
    createdAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'fs'
        get_latest_by = 'fqe'
        indexes = [
            models.Index(fields=['corp','type','by','bq']),
        ]



class FsAccount(models.Model):
    type = models.ForeignKey(
        FsType,
        related_name = 'accounts',
        on_delete = models.CASCADE,
    )
    accountNm = models.CharField(max_length=256)
    parent = models.ForeignKey(
        'self',
        related_name = 'std_childs',
        on_delete = models.CASCADE,
        blank = True, null = True,
    )
    labelEng = models.CharField(max_length=256)
    labelKor = models.CharField(max_length=256)

    class Meta:
        db_table = 'fsaccount'
        indexes = [
            models.Index(fields=['accountNm','type'])
        ]


class FsDetail(models.Model):
    fs = models.ForeignKey(
        Fs,
        related_name = 'details',
        on_delete = models.CASCADE,
    )
    account = models.ForeignKey(
        FsAccount,
        related_name = 'values',
        on_delete = models.CASCADE,
        blank = True, null = True
    )
    accountId = models.CharField(max_length=256)
    labelKor = models.CharField(max_length=256)
    value = models.BigIntegerField(null=True,blank=True)
    createdAt = models.DateField(auto_now_add=True)
    currency = models.CharField(max_length=8,null=True,blank=True)

    # for non-standard accountId
    parent = models.ForeignKey(
        FsAccount,
        related_name = 'nstd_childs',
        on_delete = models.CASCADE,
        blank = True, null = True,
    )
    matched = models.ForeignKey(
        FsAccount,
        related_name = 'nstd_siblings',
        on_delete = models.CASCADE,
        blank = True, null = True,
    )


    class Meta:
        db_table = 'fsdetail'
        get_latest_by = 'createdAt'
        indexes = [
            models.Index(fields=['accountId','fs','account']),
        ]

    @property
    def is_standard(self):
        return self.account != None


class FsDetailHistory(models.Model):
    fd = models.ForeignKey(
        FsDetail,
        related_name = 'history',
        on_delete = models.CASCADE,
    )
    prevValue = models.BigIntegerField(null=True,blank=True)
    updatedAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'fsdetail_history'
        get_latest_by = 'updatedAt'


class AccountRatio(models.Model):
    name = models.CharField(max_length=32)
    div = models.CharField(max_length=32)
    labelKor = models.CharField(max_length=128)
    syntax = models.CharField(max_length=256)
    changeIn = models.BooleanField(default=False)
    inspectResults = models.JSONField(null=True,blank=True)
    updatedAt = models.DateField(auto_now=True)

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
            # 'fs__fqe': 'fqe',
            # 'account__accountNm': 'acnt_nm',
            # 'value': 'value',
        }

    @property
    def default_fltr(self):
        return {
            'fs__corp__delistedAt__isnull' : True,
        }

    def inspect(self, **kwargs) -> dict:
        ft_div_lk_map = {
            'BS': '재무상태표',
            'CF': '현금흐름표',
            'PL': '손익계산서'
        }
        fields_inspct = {
            **self.default_fields,
            # 'fs__type__type':'ft_div',
            'fs__type__name': 'fstype',
            'fs__fqe': 'fqe',
            'id': 'fd_id'
        }
        inspect_results = {}
        for acnt_nm in self.arg_all:
            fltr = {**self.default_fltr, 'account__accountNm': acnt_nm}
            qs = (
                FsDetail.objects
                .select_related('fs','fs__corp','fs__type','account')
                .filter(**fltr)
            )
            ft_div = qs.first().fs.type.type
            dfa = pd.DataFrame.from_records(qs.values(*fields_inspct)).rename(columns=fields_inspct)

            # drop old version of fs
            idcols = [c for c in dfa.columns if c not in  ['fqe','fd_id']]
            dfa = dfa.sort_values(idcols+['fqe'], ascending=[True,False,False,True,False]).drop_duplicates(idcols)
            del dfa['fqe']

            ft_prefix_uniq = dfa.fstype.str[:-1].unique()
            if ('IS' in ft_prefix_uniq) and ('CIS' in ft_prefix_uniq):
                drop_cis = dfa.fstype.str[:-1] != 'CIS'
                dfa = dfa.loc[drop_cis]

            choice_all = []
            for oc in ['OFS', 'CFS']:
                s = get_dominant_series_by_oc(dfa, oc)
                if len(s) > 0:
                    bybq_uniq = (s.index.get_level_values('by').astype(str) + 'q' + s.index.get_level_values('bq').astype(str)).unique()
                    stock_uniq = s.index.get_level_values('stock_code').unique()
                    choice_all.append({
                        'oc': oc,
                        'label_kor': f"별도 {ft_div_lk_map[ft_div]}" if oc == 'OFS' else f"연결 {ft_div_lk_map[ft_div]}",
                        'bybq_range': [bybq_uniq.min(),bybq_uniq.max()],
                        'n_stock': len(stock_uniq),
                        'n_obs': len(s),
                        'fd_series': s.tolist()
                    })
            faid = FsAccount.objects.filter(accountNm=acnt_nm).first().id
            inspect_results[faid] = choice_all
            # {
            #     'label_kor': FsAccount.objects.filter(accountNm=acnt_nm).last().labelKor,
            #     'choices': choice_all,
            # }
        self.inspectResults = inspect_results
        self.save()
        # return inspect_results


    def get_data(self, selected, **kwargs):
        # setting inputs for query
        stock_code = kwargs.pop('stockCode', None)
        fd_id_all = []
        for k, v in selected.items():
            faid = FsAccount.objects.filter(accountNm=k).first().id
            choice_all = self.inspectResults[str(faid)]
            choice = list(filter(lambda x: x['oc'] == v, choice_all))[0]
            fd_id_all += choice['fd_series']

        fltr = {**self.default_fltr, 'id__in': sorted(fd_id_all)}
        # if stock_code != None:
        #     fltr['fs__corp__stockCode'] = stock_code

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
            .filter(**fltr)
        )

        # queryset to dataframe
        df = (
            pd.DataFrame
            .from_records(qs.values(*fields.keys()))
            .rename(columns=fields)
        )

        # colord = ['market', '']

        # calculate the values
        idcols = [c for c in df.columns if c !='value']
        # return df
        # value
        df=df.set_index(idcols).unstack('acnt_nm')
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


def get_dominant_series_by_oc(dfa, oc):
    if oc == 'OFS':
        fltr_oc = dfa.fstype.str[-1:].astype(int) % 2 == 0
    elif oc == 'CFS':
        fltr_oc = dfa.fstype.str[-1:].astype(int) % 2 == 1
    dfa_oc = dfa.loc[fltr_oc].copy()
    ft_count = dfa_oc.fstype.value_counts()
    ft_order_map = {k: i for i, k in enumerate(ft_count.keys())}
    dfa_oc['ft_order'] = dfa_oc.fstype.replace()
    del dfa_oc['fstype']
    idcols = ['stock_code', 'by', 'bq']
    dfa_oc = dfa_oc.sort_values(idcols+['ft_order'], ascending=[True,False,False,True]).drop_duplicates(idcols)
    del dfa_oc['ft_order']
    return dfa_oc.set_index(idcols)['fd_id'].rename(oc)


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

# opendart

HEADER_TGT = {
    # common fields
    '재무제표종류': 'rpt_type',
    '종목코드': 'stock_code',
    '결산기준일': 'fqe',
    # '보고서종류': 'rpt_nm',
    '통화': 'currency',
    '항목코드': 'acnt_id',
    '항목명': 'label_kor',

    # obj specific fields
    '당기 1분기말': 'value', # bs / q1
    '당기 1분기 3개월': 'value', # is, cis /  q1
    '당기 1분기': 'value', # cf / q1

    '당기 반기말': 'value', # bs / q2
    '당기 반기 3개월': 'value', # is, cis / q2
    '당기 반기': 'value', # cf / q2

    '당기 3분기말': 'value', # bs / q3
    '당기 3분기 3개월': 'value', # is, cis / q3
    '당기 3분기': 'value', # cf / q3

    '당기': 'value', # all / q4
}

OPENDART_RPTTYPE_TO_FSTYPE_ID = {
    '재무상태표, 유동/비유동법-연결재무제표': 1,
    '재무상태표, 유동/비유동법-별도재무제표': 2,
    '재무상태표, 유동성배열법-연결재무제표': 3,
    '재무상태표, 유동성배열법-별도재무제표': 4,

    '손익계산서, 기능별 분류 - 연결재무제표': 5,
    '손익계산서, 기능별 분류 - 별도재무제표': 6,
    '손익계산서, 성격별 분류 - 연결재무제표': 7,
    '손익계산서, 성격별 분류 - 별도재무제표': 8,

    '포괄손익계산서(세후기타포괄손익) - 연결재무제표': 9,
    '포괄손익계산서(세후기타포괄손익) - 별도재무제표': 10,
    '포괄손익계산서(세전기타포괄손익) - 연결재무제표(선택)': 11,
    '포괄손익계산서(세전기타포괄손익) - 별도재무제표(선택)': 12,

    '포괄손익계산서, 기능별 분류(세후기타포괄손익) - 연결재무제표': 13,
    '포괄손익계산서, 기능별 분류(세후기타포괄손익) - 별도재무제표': 14,
    '포괄손익계산서, 기능별 분류(세전기타포괄손익) - 연결재무제표(선택)': 15,
    '포괄손익계산서, 기능별 분류(세전기타포괄손익) - 별도재무제표(선택)': 16,

    '포괄손익계산서, 성격별 분류(세후기타포괄손익) - 연결재무제표': 17,
    '포괄손익계산서, 성격별 분류(세후기타포괄손익) - 별도재무제표': 18,
    '포괄손익계산서, 성격별 분류(세전기타포괄손익) - 연결재무제표(선택)': 19,
    '포괄손익계산서, 성격별 분류(세전기타포괄손익) - 별도재무제표(선택)': 20,

    '현금흐름표, 직접법 - 연결재무제표': 21,
    '현금흐름표, 직접법 - 별도재무제표': 22,
    '현금흐름표, 간접법 - 연결재무제표': 23,
    '현금흐름표, 간접법 - 별도재무제표': 24,
}

class OpendartFile(models.Model):
    by = models.IntegerField()
    bq = models.IntegerField()
    type = models.CharField(max_length=8)
    updatedAt = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'opendart_file'

    @property
    def filename(self):
        updatedAt_fn = self.updatedAt.strftime('%Y%m%d%H%M%S')
        return f"{str(self.by)}_{str(self.bq)}Q_{self.type}_{updatedAt_fn}.zip"

    def get_data(self):
        global HEADER_TGT, OPENDART_RPTTYPE_TO_FSTYPE_ID
        f = download_opendart(self.filename)
        data = []
        for ffnm in f.namelist():
            with f.open(ffnm, 'r') as ff:
                # collect data
                header = next(ff)
                header = header.decode('cp949').split('\t')
                clean_header = {i:HEADER_TGT[h] for i, h in enumerate(header) if h in HEADER_TGT.keys()}
                get_clean_row = lambda row: [x for i, x in enumerate(row.decode('cp949').split('\t')) if i in clean_header.keys()]
                corp_all = Corp.objects.all()
                sc2corp_id = {c.stockCode: c.id for c in corp_all}
                # data = []
                for row in ff:
                    d = dict(zip(clean_header.values(), get_clean_row(row)))
                    d['ft_id'] = OPENDART_RPTTYPE_TO_FSTYPE_ID[d['rpt_type']]
                    d['stock_code'] = d['stock_code'][1:-1]
                    if d['stock_code'] in sc2corp_id.keys():
                        d['corp_id'] = sc2corp_id[d['stock_code']]
                        d['value'] = int(d['value'].replace(',','')) if d['value'] != '' else None
                        data.append(d)

        # rearrange data
        data = sorted(data, key = lambda d: (d['stock_code'], d['ft_id']))
        fs_all = []
        prev = None
        for d in data:
            curr = (d['stock_code'], d['ft_id'])
            if prev != curr:
                fs_all.append({
                    'by': self.by,
                    'bq': self.bq,
                    'fqe': d['fqe'],
                    'corp_id': d['corp_id'],
                    'type_id': d['ft_id'],
                    'details': [{
                        'accountId': d['acnt_id'],
                        'labelKor': d['label_kor'],
                        'currency': d['currency'],
                        'value': d['value'],
                    }]
                })
            else:
                fs_all[-1]['details'].append({
                    'accountId': d['acnt_id'],
                    'labelKor': d['label_kor'],
                    'currency': d['currency'],
                    'value': d['value']
                })
            prev = curr
        return fs_all
