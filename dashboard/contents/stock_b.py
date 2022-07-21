from dashboard.models import *
from django.forms.models import model_to_dict

import json

class StockContents:
    def __init__(self, request):
        self.request = request
        stock_code = request.POST.get('stock_code')
        if stock_code == None:
            stock_code = '005930'

        self.corp_info = model_to_dict(Corpinfo.objects.get(stock_code=stock_code))

        # accounts
        with open('data/acnt/trees_in_id.json') as f:
            rpt_id_ord = {v: i for i, v in enumerate(list(json.load(f).keys()))}
        acnt_uniqs = Accounts.objects.filter(stock_code=stock_code).values('bybq','rpt_id').distinct()
        for u in acnt_uniqs:
            u['by'] = int(u['bybq'][:4])
            u['bq'] = int(u['bybq'][-1:])
            u.pop('bybq')
        self.uniqpairs = json.dumps(sorted(acnt_uniqs,key=lambda u: rpt_id_ord[u['rpt_id']]))
        # self.acnt_uniqs = json.dumps({
        #     'rptuniqs': sorted(set([u['rpt_id'] for u in acnt_uniqs]),key=lambda x:rpt_id_ord[x]),
        #     'byuniqs': sorted(set([u['by'] for u in acnt_uniqs])),
        #     'bquniqs': sorted(set([u['bq'] for u in acnt_uniqs])),
        #     'uniqpairs': sorted(acnt_uniqs,key=lambda x:(x['by'],x['bq'],x['rpt_id']))
        # })

    @property
    def fs(self):
        stock_code = self.request.POST.get('stock_code')
        rpt_id = self.request.POST.get('rpt_id')
        by = self.request.POST.get('by')
        bq = self.request.POST.get('bq')
        valid = (
            (stock_code != None)
            & (rpt_id != None)
            & (by != None)
            & (bq != None)
        )
        if valid:
            # return 'whats wrong'
            return FinancialStatementGenerator(self.request).get_fs()


class FinancialStatementGenerator:
    def __init__(self, request):
        self.stock_code = request.POST.get('stock_code')
        self.rpt_id = request.POST.get('rpt_id')
        self.bybq = f"{request.POST.get('by')}Q{request.POST.get('bq')}"

        with open('data/acnt/trees_in_id.json') as f:
            tree_in_id = json.load(f)[self.rpt_id]

        flat_tree = flatten_dict(tree_in_id)
        naive_flat_tree = [x.split('_')[-1] for x in flat_tree]
        self.trees = {
            'tree_in_id': tree_in_id,
            'flat_tree': flat_tree,
            'naive_flat_tree': naive_flat_tree,
        }

        with open('data/acnt/id_kr_map.json') as f:
            self.id_kr_map = json.load(f)[self.rpt_id]

    def get_fs(self):
        qs = Accounts.objects.filter(
            stock_code = self.stock_code,
            rpt_id = self.rpt_id,
            bybq = self.bybq,
        )

        # generate a skeleton fs
        fs_sk = {
            k: {
                'path': find_path(k, self.trees['tree_in_id']),
                'nm_kr': self.id_kr_map[k].replace(' ',''),
                'value': find_value(k, qs),
            } for k in self.trees['flat_tree']
        }

        # abbreviate the skeleton to standard accounts
        non_empty = [k for k in fs_sk.keys() if fs_sk[k]['value'] != None]
        p_non_empty = []
        for k in non_empty:
            p_non_empty = p_non_empty + fs_sk[k]['path']
        standards = list(set(non_empty + p_non_empty))
        fs_std = {k: v for k, v in fs_sk.items() if k in standards}

        # non standard accounts
        # childs
        new_node_nstd = lambda x: f'p_nstd_entity_{x}'
        fs_nstd = {
            d.acnt_id: {
                'path': create_path_for_nstd(d,self.trees),
                'nm_kr': d.acnt_nm_kr.replace(' ',''),
                'value': d.value,
            } for d in qs if not d.is_standard
        }
        # parents
        naive_p_nstds = list(set([k.split('_')[-1] for k in fs_nstd.keys()]))
        p_nstds = [self.trees['flat_tree'][self.trees['naive_flat_tree'].index(x)] for x in naive_p_nstds]
        fs_nstd = {
            **fs_nstd,
            **{new_node_nstd(p_nstd): {
                'path': find_path(p_nstd,self.trees['tree_in_id']) + [new_node_nstd(p_nstd)],
                'nm_kr': '미분류',
                'value': None,
            } for p_nstd in p_nstds }
        }

        ord_nstd = get_ord_nstd(fs_nstd, self.trees)
        fs_nstd = {k:fs_nstd[k] for k in ord_nstd}

        # setting order
        ord = list(fs_std.keys())
        for k_nstd, v_nstd in fs_nstd.items():
            ploc = ['p_nstd' in x for x in v_nstd['path']].index(True)
            ppath = v_nstd['path'][:ploc]
            last = [k_std for k_std, v_std in fs_std.items() if v_std['path'][:ploc] == ppath][-1]
            insert_loc = ord.index(last)
            ord.insert(insert_loc, k_nstd)

        # generate fs
        fs = {**fs_std, **fs_nstd}
        for v in fs.values():
            if len(v['path']) > 1:
                v['pid'] = v['path'][-2]
            elif len(v['path']) == 1:
                v['pid'] = None
        return {k:fs[k] for k in ord}


def find_value(k, qs):
    if k in [d.acnt_id for d in qs if d.is_standard]:
        return qs.get(acnt_id=k).value
    else:
        return None

def create_path_for_nstd(d, trees):
    new_node_nstd = lambda x: f'p_nstd_entity_{x}'
    naive_id = d.acnt_id.split('_')[-1]
    if naive_id in trees['naive_flat_tree']:
        ploc = trees['naive_flat_tree'].index(naive_id)
        pid = trees['flat_tree'][ploc]
        return find_path(pid, trees['tree_in_id']) + [new_node_nstd(pid), d.acnt_id]
    # else:
    #     return [new_node_nstd('lv0'), d.acnt_id]


def flatten_dict(tree):
    flat_dict = []
    for k, v in tree.items():
        if isinstance(v, dict):
            flat_dict = flat_dict + [k] + flatten_dict(v)
        elif isinstance(v, list):
            flat_dict = flat_dict + [k] + [vv for vv in v]
    return flat_dict

def find_path(i,d):
    for k, v in d.items():
        if k == i:
            return [k]
        elif isinstance(v, dict):
            p = find_path(i, v)
            if p:
                return [k] + p
            pass
        elif isinstance(v, list):
            for vv in v:
                if vv == i:
                    return [k] + [i]


def get_ord_nstd(fs_nstd, trees):
    # sort parents first
    ord_nstd = [k for k in fs_nstd.keys() if k[:6] == 'p_nstd']
    ord_nstd.sort(key = lambda x: trees['flat_tree'].index(x[14:]))

    # insert childs
    childs = [k for k in fs_nstd.keys() if k not in ord_nstd]
    for c in childs:
        naive_id = c.split('_')[-1]
        last = [k for k in ord_nstd if k.split('_')[-1] == naive_id][-1]
        insert_loc = ord_nstd.index(last) + 1
        ord_nstd.insert(insert_loc, c)
    return ord_nstd

# def get_ord(fs_std,fs_nstd,trees):
#     ord = list(fs_std.keys())
#     for k_nstd, v_nstd in fs_nstd.items():
#         ploc = v_nstd['path'].index('entities')
#         ppath = v_nstd['path'][:ploc]
#         insert_key = [k_std for k_std, v_std in fs_std.items() if v_std['path'][:ploc] == ppath][-1]
#         insert_loc = ord.index(insert_key)
#         ord.insert(insert_loc, k_nstd)
#     return ord
    # for k in fs_nstd.keys():
    #     naive_id = k.split('_')[-1]
    #     is_child = k[:6] == 'entity'
    #     if is_child:
    #         ord_nstd.append(k)
    #     else:




# stock_code, rpt_id, bybq = '005930', 'BS1', '2021Q1'
# fs = FinancialStatementGenerator(stock_code,rpt_id,bybq).get_fs()
