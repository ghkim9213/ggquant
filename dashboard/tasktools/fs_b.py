from bs4 import BeautifulSoup
from collections import Counter
from dashboard.models import *
from io import BytesIO
from ggquant.my_settings import ghkim

import datetime, json, os, requests, pymysql, zipfile, time
import pandas as pd


class FsTreeGenerator:


    def __init__(self):
        self.filenames = sorted([x for x in os.listdir('source/acnt') if 'kifrs' in x], reverse=True)


    def get_tree(self, typename, version):
        colnames = ['indent','labelEng', 'labelKor', 'dtype', 'ifrs_ref', 'accountId', 'accountNm']
        vs = str(version.year)+str(version.month).zfill(2)+str(version.day).zfill(2)
        df = pd.read_excel(f'source/acnt/kifrs_account_trees_{vs}.xlsx', sheet_name=typename)
        df.columns = colnames
        df = df.loc[~df.accountId.isnull()].reset_index(drop=True)
        df.indent = get_normalized_indent_level(df, typename)
        df['pid'] = get_pid(df)
        tree = [
            {
                'accountId': row['accountId'],
                'accountNm': row['accountNm'],
                'pid': row['pid'],
                'labelEng': row['labelEng'].strip(),
                'labelKor': row['labelKor'].strip(),
            } for row in df.to_dict(orient='records')
        ]
        return tree


def get_normalized_indent_level(df, typename):
    if 'BS' in typename:
        new_indent=[]
        bloc = [i for i, v in enumerate(df.accountId) if 'Abstract' in v][1:]
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


def get_pid(df):
    pids = []
    for i in range(len(df)):
        prev_indents = df.indent[:(i+1)]
        if df.indent[i] == 0:
            pid = None
            pids.append(pid)
        else:
            dfi = df[:(i+1)]
            pid_loc = dfi.loc[dfi.indent == df.indent[i]-1].index[-1]
            pid = df.loc[pid_loc].accountId
            pids.append(pid)
    return pids


class FsToday:
    def __init__(self):
        self.zf_nms = [nm for nm in get_zfnames() if 'CE' not in nm]

        # columns of interests
        # common columns
        col_root = ['재무제표종류','종목코드','결산기준일','보고서종류','통화','항목코드','항목명']

        # div-specific columns
        col_specific = [
            '당기 1분기말', # bs / q1
            '당기 1분기 3개월', # is, cis /  q1
            '당기 1분기', # cf / q1

            '당기 반기말', # bs / q2
            '당기 반기 3개월', # is, cis / q2
            '당기 반기', # cf / q2

            '당기 3분기말', # bs / q3
            '당기 3분기 3개월', # is, cis / q3
            '당기 3분기', # cf / q3

            '당기', # all / q4
        ]

        self.col_nm_kr = col_root + col_specific
        col_nm_eng = ['rpt_method_soup','stockCode','rptDate','rpt_nm','currency','accountId','labelKor'] + ['value'] * len(col_specific)
        self.col_nm_map = dict(zip(self.col_nm_kr, col_nm_eng))
        self.col_order = [
            'sjDiv', 'stockCode', 'rpt_nm',
            'by', 'bq', 'rptDate', 'accountId',
            'labelKor', 'currency', 'value', # 'last_update', 'isStandard'
        ]

        # get a list of zipfiles to download
        with open('source/acnt/acnt_zf_nms.txt', 'r') as fr:
            lines = fr.readlines()
            zf_nms_old = [line.strip() for line in lines]
        if zf_nms_old == []:
            self.zf_nms_download = self.zf_nms.copy()
        else:
            self.zf_nms_download = [nm for nm in self.zf_nms if nm not in zf_nms_old]

        # account forest
        with open('source/acnt/acnt_forest.json') as f:
            self.forest = json.load(f)

    def save_last_update(self):
        with open('source/acnt/acnt_zf_nms.txt', 'w') as fw:
            fw.truncate(0)
            for zf_nm in self.zf_nms:
                fw.write(f"{zf_nm}\n")

    def get_data(self, zf_nm):

        # download and get data
        zf = download_zipfile(zf_nm)
        print('cleaning data...')
        if zf.info['div'] == 'BS':
            fileorder = ['BS_OFS', 'BS_CFS']
        elif zf.info['div'] == 'IS':
            fileorder = ['IS_OFS', 'IS_CFS', 'CIS_OFS', 'CIS_CFS']
        elif zf.info['div'] == 'CF':
            fileorder = ['CF_OFS','CF_CFS']
        stds = get_std_acnts(zf.info['div'])
        bybq = f"{zf.info['year']}{zf.info['quarter'][1:]}{zf.info['quarter'][:1]}"
        infomap = dict(zip(zf.namelist(),fileorder))
        with open('source/acnt/sj_div.json') as f:
            sjdivmap = json.load(f)
        data = []
        fslist = []
        details = []
        for tf_nm in zf.namelist():
            with zf.open(tf_nm,'r') as tf:
                tf.info = dict(zip(['rpt_type','rpt_oc'],infomap[tf_nm].split('_')))
                header = next(tf)
                header = header.decode('cp949').split('\t')
                is_tgt = [h in self.col_nm_kr for h in header]
                id_tgt = [i for i, x in enumerate(is_tgt) if x == True]
                header_tgt = [x for i, x in enumerate(header) if i in id_tgt]
                header_tgt_eng = [self.col_nm_map[h] for h in header_tgt]
                for ll in tf:
                    line = [x for i, x in enumerate(ll.decode('cp949').split('\t')) if i in id_tgt]
                    d = dict(zip(header_tgt_eng,line))
                    rpt_method = get_rpt_method(d['rpt_method_soup'])
                    d['sjDiv'] = get_sjDiv(tf.info['rpt_type'], rpt_method, tf.info['rpt_oc'], sjdivmap)
                    d['by'] = int(zf.info['year'])
                    d['bq'] = int(zf.info['quarter'][:1])
                    # d['bybq'] = bybq
                    d['stockCode'] = d['stockCode'][1:-1]
                    d['value'] = int(d['value'].replace(',','')) if d['value'] != '' else None
                    data.append({k: d[k] for k in self.col_order})

        # rearrange data
        data = sorted(data,key=lambda d:(d['stockCode'],d['by'],d['bq'],d['sjDiv']))
        fsAll = []
        prev = None
        for d in data:
            curr = (d['stockCode'],d['by'],d['bq'],d['sjDiv'])
            if prev != curr:
                fsAll.append({
                    'stockCode': d['stockCode'],
                    'by': d['by'],
                    'bq': d['bq'],
                    'sjDiv': d['sjDiv'],
                    'rpt_nm': d['rpt_nm'],
                    'rptDate': d['rptDate'],
                    'detail': [{
                        'accountId': d['accountId'],
                        'labelKor': d['labelKor'],
                        'currency': d['currency'],
                        'value': d['value'],
                    }]
                })
            else:
                fsAll[-1]['detail'].append({
                    'accountId': d['accountId'],
                    'labelKor': d['labelKor'],
                    'currency': d['currency'],
                    'value': d['value'],
                })
            prev = curr

        print('...complete')
        return fsAll
        # return fslist, details # [{**fs,'detail':details[i]} for i, fs in enumerate(fslist)]


def get_zfnames():
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/list.do'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atags = soup.find('table','tb01').find_all('a')
    get_zfname = lambda a: a['onclick'][a['onclick'].find('(')+1:a['onclick'].find(')')].split(', ')[-1][1:-1]
    return [get_zfname(a) for a in atags]


def download_zipfile(zfname):
    print(f"downloading {zfname}...")
    download_url = 'https://opendart.fss.or.kr/cmm/downloadFnlttZip.do'
    download_payload = {'fl_nm':zfname}
    download_headers = {
        'Referer':'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do',
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    }
    r = requests.get(download_url,download_payload,headers=download_headers)
    zf = zipfile.ZipFile(BytesIO(r.content))
    info = zfname.split('_')
    dt2dtstr = lambda dt: f'{dt[:4]}-{dt[4:6]}-{dt[6:8]} {dt[8:10]}:{dt[10:12]}:{dt[12:14]}'
    zf.info = {
        'year': int(info[0]),
        'quarter': info[1],
        'div': info[2].replace('PL','IS'),
        'last_update': dt2dtstr(info[3][:-4]),
    }
    print("...complete")
    return zf


def get_std_acnts(rpt_div):
    with open('source/acnt/sj_div.json') as f:
        sjDiv_list = list(json.load(f).keys())
    with open('source/acnt/acnt_forest.json') as f:
        forest = json.load(f)
    rpt_tgt = [sjDiv for sjDiv in sjDiv_list if rpt_div in sjDiv]
    stds = []
    for sjDiv in rpt_tgt:
        for k in forest[sjDiv].keys():
            stds = stds + list(forest[sjDiv][k]['tree'].keys())
    return set(stds)


def get_rpt_method(rpt_method_soup):
    parsed = (
        rpt_method_soup
        .replace('(선택)','')
        .replace('-',',')
        .replace('(',',')
        .replace(')','')
        .replace(' ','').split(',')
    )
    return parsed[1] if len(parsed) == 3 else '/'.join([parsed[1],parsed[2][:2]])


def get_sjDiv(rpt_type,rpt_method,rpt_oc,sjdivmap):
    d = {'type': rpt_type, 'method': rpt_method, 'oc': rpt_oc}
    for k, v in sjdivmap.items():
        if v == d:
            return k



class FsManager:


    def __init__(self):
        # load sources
        global fsversion_all
        self.table_nm_all = ['fstype','fsaccount','fs','fsdetail']
        self.fsversionAll = [datetime.datetime.strptime(vs,'%Y%m%d').date() for vs in fsversion_all]
        self.fsversionAll.reverse()
        with open('source/acnt/sj_div.json') as f:
            self.fstypeAll = json.load(f)
        self.tvComb = [(fstype_nm,fsversion) for fstype_nm in self.fstypeAll.keys() for fsversion in self.fsversionAll]
        self.ftgen = FsTreeGenerator()


    def create(self, table_nm):
        if table_nm == 'fstype':
            createFsType(self, 'ggquant', ghkim['passwd'])

        elif table_nm == 'fsaccount':
            createFsAccount(self, 'ggquant', ghkim['passwd'])

        elif table_nm == 'fs':
            createFs(self, 'ggquant', ghkim['passwd'])

        else:
            print(f"No such table: '{table_nm}'")


    def resumeFs(self,**kwargs):
        createFs(self,'ggquant',ghkim['passwd'],**kwargs)

    def update(self):
        pass

    def read(self):
        pass

    def delete(self):
        pass



def createFsType(self, db_name, db_passwd):
    # colord = ['name','type','method','oc']
    records = []
    for k, v in self.fstypeAll.items():
        records.append(tuple([
            k, v['type'],v['method'],v['oc']
        ]))
    con = pymysql.connect(passwd=db_passwd,db=db_name)
    cur = con.cursor()
    cur.executemany(f'''
        INSERT INTO fstype (
            `id`, `name`, `type`, `method`, `oc`
        ) VALUES (
            NULL, %s, %s, %s, %s
        )
    ''', records)
    con.commit()
    con.close()



def createFsAccount(self, db_name, db_passwd):
    print('loading data source to create fsaccount...')
    ftgen = FsTreeGenerator()
    ftNm2ftIdx = {ft.name:ft.id for ft in FsType.objects.all()}
    comb2faIdx = {} # comb = type_id, version, accountId
    print('...complete')
    print('collecting fsaccounts...')
    records = []
    faIdx = 1
    for ftNm, ftIdx in ftNm2ftIdx.items():
        for vs in self.fsversionAll:
            tree = ftgen.get_tree(ftNm,vs)
            for a in tree:
                comb = ftIdx, vs, a['accountId']
                pComb = ftIdx, vs, a['pid']
                r = (
                    faIdx, # id
                    a['accountNm'], # accountNm
                    a['accountId'], # accountId
                    vs, # version
                    # isStandard: True for all records
                    a['labelEng'],
                    a['labelKor'],
                    # matchedWith_id: None for all records
                    None if a['pid'] == None else comb2faIdx[pComb], # parent_id
                    ftIdx, # type_id
                )
                records.append(r)
                comb2faIdx[comb] = faIdx
                faIdx += 1
    print('...complete')
    print('writing fsaccounts on db...')
    con = pymysql.connect(passwd=db_passwd,db=db_name)
    cur = con.cursor()
    cur.executemany(f'''
        INSERT INTO fsaccount (
            `id`, `accountNm`, `accountId`,
            `version`, `isStandard`, `labelEng`,
            `labelKor`, `matchedWith_id`, `parent_id`,
            `type_id`
        ) VALUES (
            %s, %s, %s,
            %s, TRUE, %s,
            %s, NULL, %s,
            %s
        )
    ''', records)
    con.commit()
    con.close()
    print('...complete')




def createFs(self, db_name, db_passwd):
    print('loading data source to create fs and fsdetail')

    con = pymysql.connect(passwd=db_passwd,db=db_name)
    cur = con.cursor()

    ftNm2ftIdx = {ft.name: ft.id for ft in FsType.objects.all()}
    stkCd2cIdx = {c.stockCode: c.id for c in Corp.objects.filter(stockCode__isnull=False)}

    accountAll = {
        ftNm: {
            vs: {} for vs in self.fsversionAll
        } for ftNm in self.fstypeAll.keys()
    }

    for fa in FsAccount.objects.all():
        accountAll[fa.type.name][fa.version][fa.accountId] = fa.id

    fsIdx_last = 0
    faIdx_last = FsAccount.objects.all().last().id
    fdIdx_last = 0
    ft = FsToday()
    print('...complete')

    print('collecting data...')
    for zf_nm in ft.zf_nms:
        # reset records
        fs_records = []
        fa_records = []
        fd_records = []

        # reset index
        fsIdx = fsIdx_last + 1
        faIdx = faIdx_last + 1
        fdIdx = fdIdx_last + 1

        # get data
        data = ft.get_data(zf_nm)
        start = time.time()

        # collect data
        print(f'collecting data...')
        for d in data:
            # table 'fs'
            d['fsIdx'] = fsIdx
            r_fs = (
                d['fsIdx'],
                d['by'],
                d['bq'],
                d['rptDate'],
                stkCd2cIdx[d['stockCode']],
                ftNm2ftIdx[d['sjDiv']],
            )
            fs_records.append(r_fs)
            fsIdx += 1
            # table 'fsaccount' and 'fsdetail'
            accountIdAll_d = [a['accountId'] for a in d['detail'] if not a['accountId'].startswith('entity')]
            accountNmAll_d = [a.split('_')[-1] for a in accountIdAll_d]
            if len(accountIdAll_d) > 0:
                faId2faVs = versionMap(accountIdAll_d,accountAll[d['sjDiv']],{})
                msvs = Counter(faId2faVs.values()).most_common(4)[0][0]
            elif len(accountIdAll_d) == 0:
                faId2faVs = {}
                rptDate = datetime.datetime.strptime(d['rptDate'],'%Y-%m-%d').date()
                tdiffs = [(rptDate-x).days for x in self.fsversionAll]
                tdiff_pos = [td for td in tdiffs if td >= 0]
                vsloc = tdiffs.index(min(tdiff_pos))
                msvs = self.fsversionAll[vsloc]
            faId_root = list(accountAll[d['sjDiv']][msvs].keys())[0]
            faId2faVs[faId_root] = msvs
            accountNmAll_d.append(faId_root.split('_')[-1])
            for a in d['detail']:
                if a['accountId'].startswith('entity'):
                    pNm = a['accountId'].split('_')[-1]
                    if pNm in accountNmAll_d:
                        pId = [faId for faId in faId2faVs.keys() if pNm == faId.split('_')[-1]][0]
                        pVs = faId2faVs[pId]
                    else:
                        pVs = msvs
                        pId = [faId for faId in accountAll[d['sjDiv']][msvs] if pNm == faId.split('_')[-1]][0]
                    a['version'] = pVs # inherit the version of parent
                    aaLoc = accountAll[d['sjDiv']][a['version']]
                    if a['accountId'] not in aaLoc.keys():
                        aaLoc[a['accountId']] = faIdx
                        r_fa = (
                            faIdx,
                            # accountNm: None for all nstd
                            a['accountId'],
                            a['version'], # version
                            # isStandard: False for all nstd
                            # labelEng: None for all nstd
                            a['labelKor'],
                            # matchedWithId: None for all (pass)
                            accountAll[d['sjDiv']][pVs][pId], # parent_id
                            ftNm2ftIdx[d['sjDiv']], # type_id
                        )
                        fa_records.append(r_fa)
                        faIdx += 1
                else:
                    a['version'] = faId2faVs[a['accountId']]

                r_fd = (
                    fdIdx,
                    a['value'], # value
                    # createdAt: CURDATE() for all
                    a['currency'],
                    accountAll[d['sjDiv']][a['version']][a['accountId']], # account_id
                    d['fsIdx'], # fs_id
                )
                fd_records.append(r_fd)
                fdIdx += 1
        print('...complete')

        # writing on db
        print('writing on db...')
        cur.executemany('''
            INSERT INTO fs (
                `id`, `by`, `bq`,
                `rptDate`, `corp_id`, `type_id`
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s
            )
        ''', fs_records)

        cur.executemany('''
            INSERT INTO fsaccount (
                `id`, `accountNm`, `accountId`,
                `version`, `isStandard`, `labelEng`,
                `labelKor`, `matchedWith_id`, `parent_id`,
                `type_id`
            ) VALUES (
                %s, NULL, %s,
                %s, FALSE, NULL,
                %s, NULL, %s,
                %s
            )
        ''', fa_records)

        cur.executemany('''
            INSERT INTO fsdetail (
                `id`, `value`, `createdAt`,
                `currency`, `account_id`, `fs_id`
            ) VALUES (
                %s, %s, CURDATE(),
                %s, %s, %s
            )
        ''', fd_records)

        con.commit()

        print('...complete')
        print(time.time()-start)

        fsIdx_last = fs_records[-1][0]
        faIdx_last = fa_records[-1][0]
        fdIdx_last = fd_records[-1][0]

    con.close()


def getMostSimilarVersion(l, d):
    scores = []
    for k, v in d.items():
        scores.append( sum([x in v.keys() for x in l])/len(l) )
    maxloc = [i for i, v in enumerate(scores) if v == max(scores)][-1]
    return list(d.keys())[maxloc], max(scores)


def versionMap(l, d, res):
    msvs, score = getMostSimilarVersion(l, d)
    if score < 1:
        ll = [x for x in l if x not in d[msvs].keys()]
        dd = d.copy()
        dd.pop(msvs)
        rres = {x: msvs for x in l if x in d[msvs].keys()}
        return versionMap(ll, dd, rres)
    elif score == 1:
        return {**res, **{x: msvs for x in l}}
