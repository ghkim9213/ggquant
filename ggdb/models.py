from .batchtools.scrappers import download_opendart_file

from collections import Counter
from django.db import models
from functools import reduce

import numpy as np
import pandas as pd
import datetime, itertools, json, re


class Corp(models.Model):
    stockCode = models.CharField(max_length=6,blank=False,null=False,unique=True)
    corpCode = models.CharField(max_length=8,blank=True,null=True)
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
    createdAt = models.DateField(auto_now_add=True)

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


# Models for financial statments

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
        f = download_opendart_file(self.filename)
        data = []
        for ffnm in f.namelist():
            with f.open(ffnm, 'r') as ff:
                is_empty_file = ff.read(1) == b''
                if not is_empty_file:
                    ff.seek(0)
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


class FsAccountSeries:

    def __init__(self, acnt_nm):
        self.acnt_nm = acnt_nm

    def get_clean_fd_series(self, oc, mkt):
        # query
        fa = FsAccount.objects.filter(accountNm=self.acnt_nm).last()
        fltr = {
            'account__accountNm': self.acnt_nm,
            'fs__type__oc': oc,
            'fs__corp__market': mkt,
        }
        qs = (
            FsDetail.objects
            .filter(**fltr)
            .select_related('fs', 'fs__corp')
        )
        if not qs.exists():
            raise ValueError(f"no fsdetails for {self.acnt_nm} in {oc}_{mkt}.")

        ft_div = qs.first().fs.type.type
        FIELDS = {
            'fs__corp__id': 'corp_id',
            'fs__corp__fye': 'fye',
            'fs__fqe': 'fqe',
            'fs__type__name': 'fstype',
            'value': 'value',
        }
        dfa = (
            pd.DataFrame
            .from_records(qs.values(*FIELDS))
            .rename(columns=FIELDS)
        )
        dfa.fqe = pd.to_datetime(dfa.fqe)

        # cleaning
        # drop duplicates in IS family
        ft_prefix_uniq = dfa.fstype.str[:-1].unique()
        if ('IS' in ft_prefix_uniq) and ('CIS' in ft_prefix_uniq):
            drop_cis = dfa.fstype.str[:-1] != 'CIS'
            dfa = dfa.loc[drop_cis]

        # drop duplicated values from dominated fstype
        ft_count = dfa.fstype.value_counts().to_dict()
        dfa['ft_order'] = dfa.fstype.replace(ft_count)
        dfa = dfa.sort_values(
            ['corp_id','fqe','ft_order'],
            ascending = [True, False, False]
        ).drop_duplicates([
            'corp_id', 'fqe'
        ])
        del dfa['ft_order'], dfa['fstype']

        # adjust by and bq based on fqe
        dfa = dfa.sort_values(['corp_id', 'fqe'])
        mgap = dfa.fqe.dt.month - dfa.fye
        ydiff = -((mgap <= 0) & (dfa.fye != 12)).astype(int)
        dfa['by'] = dfa.fqe.dt.year + ydiff
        dfa['bq'] = mgap.replace({-9:3, -6:6, -3:9, 0:12}) // 3

        # # caculate 4th quarter's value
        is_not_flow = fa.type.type == 'BS'
        if is_not_flow:
            return dfa.set_index(['corp_id','fqe'])['value']
        else:
            # caculate
            idx2fqe = (
                dfa[['corp_id','by','bq','fqe']]
                .set_index(['corp_id','by','bq'])
                .fqe.to_dict()
            )
            dfq = (
                dfa[['corp_id','by','bq','value']]
                .set_index(['corp_id','by','bq'])
                .value.unstack('bq')
            )
            dfq[4] = dfq[4] - (dfq[1] + dfq[2] + dfq[3])
            # return dfq
            dfq = dfq.stack().rename('value').to_frame()
            dfq['fqe'] = [idx2fqe[idx] for idx in dfq.index]
            return dfq.reset_index().set_index(['corp_id','fqe'])['value']


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
        if self.changeIn:
            v = labelKor_all[0]
            return f"\\text{{{self.labelKor}}}=\\text{{당기 {v}}}/\\text{{전기 {v}}}"
        else:
            for k, v in dict(zip(self.arg_all,labelKor_all)).items():
                syntax_katex = syntax_katex.replace(k,f"\\text{{{v}}}")
            syntax_katex = syntax_katex.replace('*','\times').replace("`","")
            return f"\\text{{{self.labelKor}}}={syntax_katex}"

    @property
    def operation(self):
        strargs = str(self.arg_all)[1:-1].replace("'","")
        strfunc = f"lambda {strargs}:" + self.syntax.replace("`","")
        return eval(strfunc)

    def inspect_latest_all(self, oc, mkt):
        arv_all = (
            self.values.select_related('corp')
            .filter(method=oc, corp__market=mkt, corp__delistedAt__isnull=True)
        )
        if arv_all.exists():
            df = pd.DataFrame.from_records(arv_all.values())
            df = df.sort_values(['corp_id','by','bq'], ascending=[True,False,False])
            latest_id_all = df.drop_duplicates('corp_id').id.tolist()
            return self.values.filter(id__in=latest_id_all)
        else:
            raise ValueError(f"{oc}_{mkt} has no attribute of {self.name}.")

    def get_panel(self, oc, mkt):
        if len(self.arg_all) > 1:
            s_all = []
            for acnt_nm in self.arg_all:
                fas = FsAccountSeries(acnt_nm)
                s = fas.get_clean_fd_series(oc, mkt)
                s_all.append(s.rename(acnt_nm))
            df = pd.concat(s_all,axis=1)
            panel = (
                self.operation(*[df[c] for c in self.arg_all])
                .rename('value').replace([-np.inf,np.inf],np.nan).dropna()
            )
        else:
            fas = FsAccountSeries(self.arg_all[0])
            panel = fas.get_clean_fd_series(oc, mkt)

        if self.changeIn:
            panel = panel.reset_index().sort_values(['corp_id','fqe'])
            panel['prev_fqe'] = panel.groupby('corp_id').fqe.shift(1)
            panel['prev_value'] = panel.groupby('corp_id').value.shift(1)
            panel = panel.dropna()
            big_gap = (panel.fqe - panel.prev_fqe) > '92 days'
            panel = panel.loc[~big_gap]
            panel['ar'] = panel.value / panel.prev_value
            panel = (
                panel.set_index(['corp_id','fqe']).ar
                .replace([-np.inf,np.inf],np.nan)
                .dropna().rename('value')
            )
        return panel


    def get_aggregate_time_series(self, oc, mkt, **kwargs):
        qs = self.values.filter(method=oc, corp__market=mkt)
        if not qs.exists():
            raise ValueError(f"no {self.name} values for {oc} {mkt}.")
        df = pd.DataFrame.from_records(qs.values())
        bounds = kwargs.pop('bounds', None)
        if bounds != None:
            lb, ub = df.value.quantile(bounds).tolist()
            winsor = (df.value >= lb) & (df.value <= ub)
            df = df[winsor]
        aggmethod = kwargs.pop('method', None)
        if aggmethod == None:
            raise ValueError('the aggregate method should be required.')
        elif aggmethod == 'mean':
            return df.groupby(['by','bq']).value.mean()
        elif aggmethod == 'median':
            return df.groupby(['by','bq']).value.median()

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


OC_MKT_ORD = [
    ('CFS', 'KOSPI'),
    ('OFS', 'KOSPI'),
    ('CFS', 'KOSDAQ'),
    ('OFS', 'KOSDAQ'),
]


class AccountRatioValue(models.Model):
    ar = models.ForeignKey(
        AccountRatio,
        related_name = 'values',
        on_delete = models.CASCADE,
    )
    corp = models.ForeignKey(
        Corp,
        related_name = 'account_ratios',
        on_delete = models.CASCADE,
    )
    fqe = models.DateField(blank=True, null=True)
    oc = models.CharField(max_length=3)
    value = models.FloatField()
    isLatest = models.BooleanField(default=False)
    createdAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'account_ratio_value'
        get_latest_by = 'fqe'
        indexes = [
            models.Index(fields=['corp','ar','fqe','oc','isLatest']),
        ]



class AccountRatioValueHistory(models.Model):
    arv = models.ForeignKey(
        AccountRatioValue,
        related_name = 'history',
        on_delete = models.CASCADE,
    )
    prevValue = models.FloatField(null=True,blank=True)
    updatedAt = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'account_ratio_value_history'
        get_latest_by = 'updatedAt'
