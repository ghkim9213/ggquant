from .batchtools.account_ratio import *

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
    idcols = ['corp_id', 'by', 'bq']
    dfa_oc = dfa_oc.sort_values(idcols+['ft_order'], ascending=[True,False,False,True]).drop_duplicates(idcols)
    del dfa_oc['ft_order']
    return dfa_oc.set_index(idcols)['value']#.rename(oc)


self = AccountRatioManager()
ar = self.ar_all.last()
acnt_nm = ar.arg_all[0]
ft_type = FsAccount.objects.filter(accountNm=acnt_nm).last().type.type
is_flow = ft_type != 'BS'
arv_all = ar.values.all()
comb2arv = {(arv.ar_id, arv.corp_id, arv.by, arv.bq, arv.method): arv for arv in arv_all}
oc = 'CFS'
fields = {
    'fs__corp__id': 'corp_id',
    'fs__by': 'by',
    'fs__bq': 'bq',
    'fs__type__name': 'fstype',
    'fs__fqe': 'fqe',
    'value': 'value',
}

fltr = {
    'fs__corp__delistedAt__isnull': True,
    'account__accountNm': acnt_nm
}
qs = (
    FsDetail.objects
    .select_related('fs','fs__corp','fs__type','account')
    .filter(**fltr)
)
ft_div = qs.first().fs.type.type
dfa = pd.DataFrame.from_records(qs.values(*fields)).rename(columns=fields)
# if is_flow:
indexes = dfa.columns[:-1]

# drop old version of fs
idcols = [c for c in dfa.columns if c not in  ['fqe','value']]
dfa = dfa.sort_values(idcols+['fqe'], ascending=[True,False,False,True,False]).drop_duplicates(idcols)
del dfa['fqe']

ft_prefix_uniq = dfa.fstype.str[:-1].unique()
if ('IS' in ft_prefix_uniq) and ('CIS' in ft_prefix_uniq):
    drop_cis = dfa.fstype.str[:-1] != 'CIS'
    dfa = dfa.loc[drop_cis]

s = get_dominant_series_by_oc(dfa, oc)

dfq = s.sort_index().unstack('bq')
dfq[4] = dfq[4] - (dfq[1]+dfq[2]+dfq[3])

# s_all.append(s.rename(acnt_nm))

    #
    # if ar.changeIn:
    #     df = s.reset_index().sort_values(['corp_id','by','bq'])
    #     df['prev_value'] = df.value.groupby(df.corp_id).shift(1)
    #     ym = df.by.astype(str) + (df.bq*3).astype(str).str.zfill(2)
    #     df['ym'] = pd.to_datetime(ym,format='%Y%m')
    #     df['prev_ym'] = df.ym.groupby(df.corp_id).shift(1)
    #     df = df.dropna()
    #     big_gap = (df.ym - df.prev_ym) > '92 days'
    #     df = df.loc[~big_gap]
    #     df['ar'] = df.value / df.prev_value
    #     ss = df.set_index(['corp_id','by','bq']).ar
    #     new_arv_all = (
    #         ss.rename('value').replace([-np.inf,np.inf],np.nan).dropna()
    #         .reset_index().to_dict(orient='records')
    #     )
    # else:
    #     df = pd.concat(s_all,axis=1)
    #     new_arv_all = (
    #         ar.operation(*[df[c] for c in ar.arg_all])
    #         .rename('value').replace([-np.inf,np.inf],np.nan).dropna()
    #         .reset_index().to_dict(orient='records')
    #     )
    # for new_arv in new_arv_all:
    #     arv = comb2arv.pop(
    #         (
    #             ar.id,
    #             new_arv['corp_id'],
    #             new_arv['by'],
    #             new_arv['bq'],
    #             oc,
    #         ), None
    #     )
    #     if arv == None:
    #         arv_created.append(AccountRatioValue(**{
    #             'ar_id': ar.id,
    #             **new_arv,
    #             'method': oc,
    #         }))
    #     else:
    #         if arv.value != new_arv['value']:
    #             arvh_all.append(AccountRatioValueHistory(
    #                 arv = arv,
    #                 prevValue = arv.value
    #             ))
    #             arv.value = new_arv['value']
    #             arv_updated.append(arv)
