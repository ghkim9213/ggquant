from bs4 import BeautifulSoup
from collections import Counter
from dashboard.models import *
from django.forms.models import model_to_dict
from io import BytesIO
from itertools import islice

import datetime, json, os, requests, zipfile, time
import pandas as pd


class FsTree:

    def __init__(self, ftnm):
        self.fs_version_all = ['20130331', '20171001', '20180720', '20191028']
        self.ftnm = ftnm
        self._all = None

    def collect_all(self):
        colnames = ['indent','label_eng', 'label_kor', 'dtype', 'ifrs_ref', 'acnt_id', 'acnt_nm']
        tree_all = []
        for vs in self.fs_version_all:
            df = pd.read_excel(f'source/acnt/kifrs_account_trees_{vs}.xlsx', sheet_name=self.ftnm)
            df.columns = colnames
            df = df.loc[~df.acnt_id.isnull()].reset_index(drop=True)
            df.indent = get_normalized_indent_level(df, self.ftnm)
            df['pnm'] = get_parent_names(df)
            tree_all.append({
                row['acnt_nm'].strip(): {
                    # 'acnt_id': row['acnt_id'].strip(),
                    'pnm': row['pnm'].strip() if row['pnm'] != None else None,
                    'label_eng': row['label_eng'].strip(),
                    'label_kor': row['label_kor'].strip()
                } for row in df.to_dict(orient='records')
            })
        self._all = tree_all

    def get_dominant_tree(self):
        dominant = self._all[-1].copy()
        oldest = self._all[0].copy()
        acnt_nm_dom = [a.lower() for a in dominant.keys()]
        acnt_nm_diff = [a for a in oldest.keys() if a.lower() not in acnt_nm_dom]
        for acnt_nm in acnt_nm_diff:
            ancestor_all = get_all_ancestor(acnt_nm,oldest,[])
            find, pnm = False, None
            for ancestor in ancestor_all:
                if ancestor in dominant.keys():
                    find = True
                    pnm = ancestor
                    break
            if find == False:
                raise KeyError(acnt_nm)
            oldest[acnt_nm]['pnm'] = pnm
            oldest[acnt_nm]['oldest'] = True
            dominant[acnt_nm] = oldest[acnt_nm]
        if len(dominant.keys()) > len(set(dominant.keys())):
            raise ValueError('not unique account name')
        return dominant

def get_normalized_indent_level(df, ftnm):
    if ftnm.startswith('BS'):
        new_indent=[]
        bloc = [i for i, v in enumerate(df.acnt_id) if 'Abstract' in v][1:]
        range_g1 = range(bloc[0], bloc[1])
        range_g2 = range(bloc[1], bloc[2])
        range_g3 = range(bloc[2], len(df)-1)
        for rng in [range_g1, range_g2, range_g3]:
            dfn = df.loc[rng]
            u_indent = dfn.indent.unique()
            new_indent_n = dfn.indent.replace({v:(i+1) for i, v in enumerate(u_indent)}).tolist()
            new_indent = new_indent + new_indent_n
        return [0] + new_indent + [1]
    else:
        u_indent = df.indent.unique()
        return df.indent.replace({v:i for i, v in enumerate(u_indent)}).tolist()


def get_parent_names(df):
    pnms = []
    for i in range(len(df)):
        prev_indent_all = df.indent[:(i+1)]
        if df.indent[i] == 0:
            pnm = None
            pnms.append(pnm)
        else:
            dfi = df[:(i+1)]
            pnm_loc = dfi.loc[dfi.indent == df.indent[i]-1].index[-1]
            pnm = df.loc[pnm_loc].acnt_nm
            pnms.append(pnm)
    return pnms


def get_all_ancestor(acnt_nm, tree, prev_result):
    pnm = tree[acnt_nm]['pnm']
    if pnm != None:
        prev_result.append(pnm)
        return get_all_ancestor(pnm, tree, prev_result)
    else:
        return prev_result


class FsTypeManager:

    def __init__(self):
        self.FSTYPE_DATA = [
            (1, 'BS1', 'BS', '유동/비유동법', 'CFS', True),
            (2, 'BS2', 'BS', '유동/비유동법', 'OFS', True),
            (3, 'BS3', 'BS', '유동성배열법', 'CFS', True),
            (4, 'BS4', 'BS', '유동성배열법', 'OFS', True),
            (5, 'IS1', 'PL', '기능별분류', 'CFS', True),
            (6, 'IS2', 'PL', '기능별분류', 'OFS', True),
            (7, 'IS3', 'PL', '성격별분류', 'CFS', True),
            (8, 'IS4', 'PL', '성격별분류', 'OFS', True),
            (9, 'CIS1', 'PL', '세후', 'CFS', True),
            (10, 'CIS2', 'PL', '세후', 'OFS', True),
            (11, 'CIS3', 'PL', '세전', 'CFS', False),
            (12, 'CIS4', 'PL', '세전', 'OFS', False),
            (13, 'DCIS1', 'PL', '기능별분류/세후기타포괄손익', 'CFS', True),
            (14, 'DCIS2', 'PL', '기능별분류/세후기타포괄손익', 'OFS', True),
            (15, 'DCIS3', 'PL', '기능별분류/세전기타포괄손익', 'CFS', False),
            (16, 'DCIS4', 'PL', '기능별분류/세전기타포괄손익', 'OFS', False),
            (17, 'DCIS5', 'PL', '성격별분류/세후기타포괄손익', 'CFS', True),
            (18, 'DCIS6', 'PL', '성격별분류/세후기타포괄손익', 'OFS', True),
            (19, 'DCIS7', 'PL', '성격별분류/세전기타포괄손익', 'CFS', False),
            (20, 'DCIS8', 'PL', '성격별분류/세전기타포괄손익', 'OFS', False),
            (21, 'CF1', 'CF', '직접법', 'CFS', True),
            (22, 'CF2', 'CF', '직접법', 'OFS', True),
            (23, 'CF3', 'CF', '간접법', 'CFS', True),
            (24, 'CF4', 'CF', '간접법', 'OFS', True),
        ]

    def update(self):
        if FsType.objects.all().exists():
            print('no update for the model FsType')
        else:
            print('updating fstype data...')
            fields = ['id', 'name', 'type', 'method', 'oc', 'required']
            obj_all = [FsType(**dict(zip(fields, d))) for d in self.FSTYPE_DATA]
            FsType.objects.bulk_create(obj_all)
            print('...update complete!')


class OpendartFileManager:

    def __init__(self):
        self.odf_all = OpendartFile.objects.all()
        self._updated_file_all = []

    def update(self):
        print('updating opendart_file data...')
        fnm_all = [fnm for fnm in get_odfnm_today() if 'CE' not in fnm]
        new_data_list = [fnm[:-4].split('_') for fnm in fnm_all]
        new_data = [{
            'by': int(by),
            'bq': int(bq[:-1]),
            'type': type,
            'updatedAt': datetime.datetime.strptime(updatedAt,'%Y%m%d%H%M%S')
        } for by, bq, type, updatedAt in new_data_list]

        odf_created, odf_updated = [], []
        comb2odf = {(odf.by, odf.bq, odf.type): odf for odf in self.odf_all}
        for d in new_data:
            odf = comb2odf.pop((d['by'],d['bq'],d['type']) ,None)
            if odf == None:
                new_odf = OpendartFile(
                    by = d['by'],
                    bq = d['bq'],
                    type = d['type'],
                    updatedAt = d['updatedAt']
                )
                odf_created.append(new_odf)
                self._updated_file_all.append(new_odf)
            else:
                if odf.updatedAt != d['updatedAt']:
                    odf.updatedAt = d['updatedAt']
                    odf_updated.append(odf)
                    self._updated_file_all.append(odf)
                # odf_updated.a

        if len(odf_created) > 0:
            OpendartFile.objects.bulk_create(odf_created)
            print(f"...{len(odf_created)} opendart_files were created.")

        if len(odf_updated) > 0:
            OpendartFile.objects.bulk_update(odf_updated, ['updatedAt'])
            print(f"...{len(odf_updated)} opendart_files were updated.")

        print('...update complete!')


def get_odfnm_today():
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/list.do'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atags = soup.find('table','tb01').find_all('a')
    get_filename = lambda a: a['onclick'][a['onclick'].find('(')+1:a['onclick'].find(')')].split(', ')[-1][1:-1]
    return [get_filename(a) for a in atags]


class FsAccountManager:

    def __init__(self):
        ft_all = FsType.objects.all()
        self.ftid2ftnm = {ft.id: ft.name for ft in ft_all}
        # self.ftnm_all = FsType.objects.all().values_list('name', flat=True)

    def update(self):
        if FsAccount.objects.all().exists():
            print('no update for the model FsAccount.')
            # raise ValueError('fsaccount already exists. please reset the table before update.')
        else:
            print('updating fsaccount data...')
            obj_all = []
            faid = 1
            for ftid, ftnm in self.ftid2ftnm.items():
                print(f'...generating fstree for {ftnm}')
                fstree = FsTree(ftnm)
                fstree.collect_all()
                dominant = fstree.get_dominant_tree()
                acnt_nm2faid = {}
                for k, v in dominant.items():
                    obj_all.append(FsAccount(**{
                        'id': faid,
                        'type_id': ftid,
                        'accountNm': k,
                        # 'accountId': v['acnt_id'],
                        'parent_id': acnt_nm2faid[v['pnm']] if v['pnm'] != None else None,
                        'labelEng': v['label_eng'],
                        'labelKor': v['label_kor'],
                    }))
                    acnt_nm2faid[k] = faid
                    faid += 1
            FsAccount.objects.bulk_create(obj_all)
            print('...update complete!')


class FsManager:

    def __init__(self, odf):
        self.odf = odf
        self._details = None
        # pass

    def update(self, **kwargs):
        print(f"updating fs data from {self.odf.filename}...")
        self._details = []

        fs_all = Fs.objects.select_related('corp','type').all()
        new_fsid = 1 if not fs_all.exists() else fs_all.last().id + 1
        fs_odf = fs_all.filter(by=self.odf.by, bq=self.odf.bq, type__type=self.odf.type)
        comb2fs = {(fs.by, fs.bq, fs.fqe.strftime('%Y-%m-%d'), fs.corp_id, fs.type_id): fs for fs in fs_odf}
        fs_created = []

        data = self.odf.get_data()
        for d in data:
            fs = comb2fs.pop((d['by'], d['bq'], d['fqe'], d['corp_id'], d['type_id']), None)
            if fs == None:
                new_fs = Fs(
                    id = new_fsid,
                    by = d['by'],
                    bq = d['bq'],
                    fqe = d['fqe'],
                    corp_id = d['corp_id'],
                    type_id = d['type_id']
                )
                fs_created.append(new_fs)
                new_fsid += 1

            # drop duplicates in details
            dd_uniq = []
            dd_acnt_id_uniq = []
            for dd in d['details']:
                if dd['accountId'] not in dd_acnt_id_uniq:
                    dd_acnt_id_uniq.append(dd['accountId'])
                    dd_uniq.append(dd)
                # else:
                #     d['details'].remove(dd)
                # dd['accountId']
            self._details += [{
                'fs_id': new_fs.id if fs == None else fs.id,
                'type_id': d['type_id'],
                **dd
            } for dd in dd_uniq]

        if len(fs_created) > 0:
            Fs.objects.bulk_create(fs_created)
            print(f"...{len(fs_created)} financial statements are created.")

        else:
            print('...no new financial statements.')
        print('...update complete!')

    def update_details(self):
        print(f"updating fsdetail data from {self.odf.filename}...")
        # if Fs.objects.all().exists():
        if self._details == None:
            raise ValueError('update() should be preceded to update_details().')

        acnt_odf = FsAccount.objects.select_related('type').filter(type__type=self.odf.type)
        comb2fa = {(fa.accountNm.lower(), fa.type.id): fa for fa in acnt_odf}
        # is_first_update = not FsDetail.objects.all().exists()
        for fd in self._details:
            ftid = fd.pop('type_id')
            if not fd['accountId'].startswith('entity'):
                acnt_nm = fd['accountId'].split('_')[-1]
                fd['account_id'] = comb2fa[(acnt_nm.lower(),ftid)].id
            else:
                pnm = fd['accountId'].split('_')[-1]
                fd['parent_id'] = comb2fa[(pnm.lower(),ftid)].id

        fsid_all = list(set([fd['fs_id'] for fd in self._details]))
        fd_all = FsDetail.objects.select_related('fs').filter(fs_id__in=fsid_all)
        comb2fd = {(fd.accountId, fd.fs_id): fd for fd in fd_all}
        fd_updated, fdh_all, fd_created = [], [], []
        for new_fd in self._details:
            fd = comb2fd.pop((new_fd['accountId'], new_fd['fs_id']), None)
            if fd == None:
                fd_created.append(FsDetail(**new_fd))
            else:
                if fd.value != new_fd['value']:
                    fdh_all.append(FsDetailHistory(
                        fd = fd,
                        prevValue = fd.value
                    ))
                    fd.value = new_fd['value']
                    fd_updated.append(fd)

        batch_size = 100000
        if len(fd_updated) > 0:
            while True:
                print(f"...{len(fd_updated)} rows were left to be updated.")
                batch_u = list(islice(fd_updated, batch_size))
                if not batch_u:
                    break
                FsDetail.objects.bulk_update(batch_u, ['value'], batch_size)
                fd_updated = fd_updated[batch_size:]
        else:
            print('...no change in fsdetail.')

        if len(fdh_all) > 0:
            while True:
                print(f"...{len(fdh_all)} new history were left to be created.")
                batch_h = list(islice(fdh_all, batch_size))
                if not batch_h:
                    break
                FsDetailHistory.objects.bulk_create(batch_h, batch_size)
                fdh_all = fdh_all[batch_size:]


        if len(fd_created) > 0:
            while True:
                print(f"...{len(fd_created)} rows were left to be created.")
                batch_c = list(islice(fd_created, batch_size))
                if not batch_c:
                    break
                FsDetail.objects.bulk_create(batch_c, batch_size)
                fd_created = fd_created[batch_size:]
        else:
            print('...no new fsdetail.')
        print('...update complete!')
