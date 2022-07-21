from .models import Ticks
from ggquant.my_settings import dart_crtfc_key

from django.db.models import F, Sum, Min, Max

from bs4 import BeautifulSoup
from copy import deepcopy
from io import BytesIO
from math import ceil
import datetime, csv, requests, json, zipfile, xmltodict
import pandas as pd

class TimeReader:
    def __init__(self, date):
        self.date = '-'.join([date[:4],date[4:6],date[6:]])
        self.mkt_open = '08:29:59'
        self.mkt_close = '16:00:00'
        self.dtformat = '%Y-%m-%d %H:%M:%S'
        self.now = f'{self.date} {self.mkt_open}'

    def ticktock(self):
        self.now = str(
            datetime.datetime.strptime(self.now,self.dtformat)
            + datetime.timedelta(seconds=1)
        )
        if self.now[-2:] == '00':
            with open('data/temp/minute_now.txt','w') as f:
                f.truncate(0)
                f.write(self.now)
        return self.now

class MinuteAlarm:
    def __init__(self):
        self.prev_minute = None

    def ringring(self):
        with open('data/temp/minute_now.txt','r') as f:
            current_minute = f.readline()
        status = False
        if self.prev_minute == None:
            pass
        elif self.prev_minute == current_minute:
            pass
        elif self.prev_minute != current_minute:
            status = True
        self.prev_minute = current_minute
        return status

class TickReader:
    def __init__(self, date):
        with open('data/temp/start_row.txt','w') as f:
            f.truncate(0)
        with open('data/temp/minute_now.txt','w') as f:
            f.truncate(0)
        self.reader = csv.reader(open(f'data/{date}.csv'))
        next(self.reader)

    def ticktock(self, now):
        start_row = open('data/temp/start_row.txt','r').readline()
        is_initial_tp = start_row == '' # is this initial time point?

        dt2dtstr = lambda dt: ' '.join([
            '-'.join([dt[:4],dt[4:6],dt[6:8]]),
            ':'.join([dt[8:10],dt[10:12],dt[12:14]])
        ])

        if is_initial_tp:
            dt_start_row = None
        else:
            start_row = start_row.split(',')
            dt_start_row = dt2dtstr(start_row[0])

        get_items = lambda r: {
            'market': r[1],
            'stock_code': r[2],
            'price': int(r[3]),
            'side': r[4],
            'volume': int(r[5])
        }
        create_row = lambda r: {
            'datetime': dt2dtstr(r[0]),
            'items': [get_items(r)]
        }

        invalid = (dt_start_row != now) & (dt_start_row != None)

        if invalid:
            status = '013' # no data
            data = {
                'datetime': now,
                'items': None,
            }
            res = {
                'status': status,
                'data': data
            }
        else:
            status = '010' # normal operation
            if dt_start_row == None:
                data = None
            elif dt_start_row == now:
                data = create_row(start_row)
            for r in self.reader:
                if data == None:
                    data = create_row(r)
                elif dt2dtstr(r[0]) == now:
                    data['items'].append(get_items(r))
                else:
                    with open('data/temp/start_row.txt','w') as f:
                        f.truncate(0)
                        f.write(','.join(r))
                    break
        res = {
            'status': status,
            'data': data
        }
        return res

def get_minutes(now):
    dtformat = '%Y-%m-%d %H:%M:%S'
    end_at = datetime.datetime.strptime(now,dtformat)
    start_at = end_at - datetime.timedelta(minutes=1)
    qs = Ticks.objects.filter(datetime__gte=start_at,datetime__lt=end_at)
    if len(qs) > 0:
        status = '010'
        agg0 = qs.annotate(volume_mt=F('price')*F('volume')).values('stock_code').annotate(
            high = Max('price'),
            low = Min('price'),
            volume = Sum('volume'),
            volume_m = Sum('volume_mt')
        ).order_by('stock_code')
        mmlocs = qs.values('stock_code').annotate(Max('id'),Min('id'))
        maxlocs = [m['id__max'] for m in mmlocs]
        minlocs = [m['id__min'] for m in mmlocs]
        agg1 = qs.filter(id__in=minlocs).annotate(open=F('price')).values('stock_code','open').order_by('stock_code')
        agg2 = qs.filter(id__in=maxlocs).annotate(close=F('price')).values('stock_code','close').order_by('stock_code')
        data = {
            'datetime': str(start_at)[:-3],
            'items': [{**z[0],**z[1],**z[2]} for z in zip(agg0,agg1,agg2)]
        }
    else:
        status = '013'
        data = {
            'datetime': str(start_at)[:-3],
            'items': None,
        }
    res = {
        'status': status,
        'data': data,
    }
    return res

# fundamentals
def get_kind(marketType):
    url = 'https://kind.krx.co.kr/corpgeneral/corpList.do'
    if marketType == 'KOSPI':
        marketType_payload = 'stockMkt'
    elif marketType == 'KOSDAQ':
        marketType_payload = 'kosdaqMkt'
    payload = {
        'method':'download',
        'pageIndex':'1',
        'currentPageSize':'3000',
        'marketType':marketType_payload,
    }
    res = requests.post(url,payload)
    table = pd.read_html(res.content)[0]
    table.columns = ['corp_name','stock_code','ind','product','listed_at','fye','ceo','homepage','district']
    table['market'] = marketType
    table['stock_code'] = table['stock_code'].astype(str).str.zfill(6)
    table['fye'] = table['fye'].str[:-1].astype(int)
    return json.loads(table.to_json(force_ascii=False,orient='records'))

def get_dart():
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    r = requests.get(url,{'crtfc_key':dart_crtfc_key})
    f = BytesIO(r.content)
    zf = zipfile.ZipFile(f)
    xml = zf.read(zf.namelist()[0]).decode('utf-8')
    data = xmltodict.parse(xml)['result']['list']
    return [dict(d) for d in data if d['stock_code'] != None]

class CorpinfoToday:
    def __init__(self):
        self.kind = get_kind('KOSPI') + get_kind('KOSDAQ')
        self.dart = get_dart()

    def get_corp_info(self):
        data = self.kind
        for d in data:
            corp_code = [a['corp_code'] for a in self.dart if a['stock_code'] == d['stock_code']]
            if len(corp_code) == 1:
                d['corp_code'] = corp_code[0]
            elif len(corp_code) == 0:
                d['corp_code'] = None
        return data


class AccountToday:
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
        col_nm_eng = ['rpt_method_soup','stock_code','rpt_date','rpt_nm','currency','acnt_id','acnt_nm_kr'] + ['value'] * len(col_specific)
        self.col_nm_map = dict(zip(self.col_nm_kr, col_nm_eng))
        # self.col_order = [
        #     'rpt_info', 'stock_code', 'rpt_nm',
        #     'rpt_date', 'acnt_id', 'is_standard',
        #     'acnt_nm_kr', 'value', 'currency',
        #     'last_update',
        # ]
        self.col_order = [
            'rpt_id', 'stock_code', 'rpt_nm',
            'bybq', 'rpt_date', 'acnt_id',
            'is_standard', 'acnt_nm_kr', 'currency',
            'value', 'last_update',
        ]

        # get a list of zipfiles to download
        with open('data/acnt/acnt_zf_nms.txt', 'r') as fr:
            lines = fr.readlines()
            zf_nms_old = [line.strip() for line in lines]
        if zf_nms_old == []:
            self.zf_nms_download = self.zf_nms.copy()
        else:
            self.zf_nms_download = [nm for nm in self.zf_nms if nm not in zf_nms_old]

        # account tree
        with open('data/acnt/trees_in_id.json') as f:
            self.tree = json.load(f)

        # name map
        with open('data/acnt/id_kr_map.json') as f:
            self.id_kr_map = json.load(f)

    def save_last_update(self):
        with open('data/acnt/acnt_zf_nms.txt', 'w') as fw:
            fw.truncate(0)
            for zf_nm in self.zf_nms:
                fw.write(f"{zf_nm}\n")

    def get_data(self, zf_nm):
        zf = download_zipfile(zf_nm)
        print('cleaning data...')
        if zf.info['div'] == 'BS':
            fileorder = ['BS_OFS', 'BS_CFS']
        elif zf.info['div'] == 'IS':
            fileorder = ['IS_OFS', 'IS_CFS', 'CIS_OFS', 'CIS_CFS']
        elif zf.info['div'] == 'CF':
            fileorder = ['CF_OFS','CF_CFS']
        # elif zf.info['div'] == 'CE':
        #     fileorder = ['CE_OFS','CE_CFS']
        bybq = f"{zf.info['year']}{zf.info['quarter'][1:]}{zf.info['quarter'][:1]}"
        infomap = dict(zip(zf.namelist(),fileorder))
        data = []
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
                    rpt_id = rpt_id_map(tf.info['rpt_type'], rpt_method, tf.info['rpt_oc'])
                    # rpt_info = f"{rpt_id}_{zf.info['year']}_{zf.info['quarter']}"
                    acnt_path = find_path(d['acnt_id'], self.tree[rpt_id])
                    # if d['value'] == '':
                    #     continue
                    # else:
                    d['rpt_id'] = rpt_id
                    d['bybq'] = bybq
                    d['is_standard'] = int(False)
                    if acnt_path:
                        d['is_standard'] = int(True)
                        d['acnt_nm_kr'] = self.id_kr_map[rpt_id][d['acnt_id']]
                    d['last_update'] = zf.info['last_update']
                    d['stock_code'] = d['stock_code'][1:-1]
                    if d['value'] == '':
                        d['value'] = None
                    else:
                        d['value'] = int(d['value'].replace(',',''))
                    data.append({k: d[k] for k in self.col_order})
        print('...complete')
        return data

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

def rpt_id_map(rpt_type, rpt_method, rpt_oc):
    if (rpt_type == 'BS') & (rpt_method == '유동/비유동법') & (rpt_oc == 'CFS'):
        rpt_id = 'BS1'
    elif (rpt_type == 'BS') & (rpt_method == '유동/비유동법') & (rpt_oc == 'OFS'):
        rpt_id = 'BS2'
    elif (rpt_type == 'BS') & (rpt_method == '유동성배열법') & (rpt_oc == 'CFS'):
        rpt_id = 'BS3'
    elif (rpt_type == 'BS') & (rpt_method == '유동성배열법') & (rpt_oc == 'OFS'):
        rpt_id = 'BS4'

    elif (rpt_type == 'IS') & (rpt_method == '기능별분류') & (rpt_oc == 'CFS'):
        rpt_id = 'IS1'
    elif (rpt_type == 'IS') & (rpt_method == '기능별분류') & (rpt_oc == 'OFS'):
        rpt_id = 'IS2'
    elif (rpt_type == 'IS') & (rpt_method == '성격별분류') & (rpt_oc == 'CFS'):
        rpt_id = 'IS3'
    elif (rpt_type == 'IS') & (rpt_method == '성격별분류') & (rpt_oc == 'OFS'):
        rpt_id = 'IS4'

    elif (rpt_type == 'CIS') & (rpt_method == '세후기타포괄손익') & (rpt_oc == 'CFS'):
        rpt_id = 'CIS1'
    elif (rpt_type == 'CIS') & (rpt_method == '세후기타포괄손익') & (rpt_oc == 'OFS'):
        rpt_id = 'CIS2'
    elif (rpt_type == 'CIS') & (rpt_method == '세전기타포괄손익') & (rpt_oc == 'CFS'):
        rpt_id = 'CIS3'
    elif (rpt_type == 'CIS') & (rpt_method == '세전기타포괄손익') & (rpt_oc == 'OFS'):
        rpt_id = 'CIS4'

    elif (rpt_type == 'CIS') & (rpt_method == '기능별분류/세후') & (rpt_oc == 'CFS'):
        rpt_id = 'DCIS1'
    elif (rpt_type == 'CIS') & (rpt_method == '기능별분류/세후') & (rpt_oc == 'OFS'):
        rpt_id = 'DCIS2'
    elif (rpt_type == 'CIS') & (rpt_method == '기능별분류/세전') & (rpt_oc == 'CFS'):
        rpt_id = 'DCIS3'
    elif (rpt_type == 'CIS') & (rpt_method == '기능별분류/세전') & (rpt_oc == 'OFS'):
        rpt_id = 'DCIS4'
    elif (rpt_type == 'CIS') & (rpt_method == '성격별분류/세후') & (rpt_oc == 'CFS'):
        rpt_id = 'DCIS5'
    elif (rpt_type == 'CIS') & (rpt_method == '성격별분류/세후') & (rpt_oc == 'OFS'):
        rpt_id = 'DCIS6'
    elif (rpt_type == 'CIS') & (rpt_method == '성격별분류/세전') & (rpt_oc == 'CFS'):
        rpt_id = 'DCIS7'
    elif (rpt_type == 'CIS') & (rpt_method == '성격별분류/세전') & (rpt_oc == 'OFS'):
        rpt_id = 'DCIS8'

    elif (rpt_type == 'CF') & (rpt_method == '직접법') & (rpt_oc == 'CFS'):
        rpt_id = 'CF1'
    elif (rpt_type == 'CF') & (rpt_method == '직접법') & (rpt_oc == 'OFS'):
        rpt_id = 'CF2'
    elif (rpt_type == 'CF') & (rpt_method == '간접법') & (rpt_oc == 'CFS'):
        rpt_id = 'CF3'
    elif (rpt_type == 'CF') & (rpt_method == '간접법') & (rpt_oc == 'OFS'):
        rpt_id = 'CF4'

    return rpt_id


class AccountTree:
    def __init__(self, rpt_id):
        self.rpt_id = rpt_id
        with open('data/acnt/typo.json','r') as jsfile:
            typomap = json.load(jsfile)
        df = pd.read_excel('data/acnt/acnt_idnm_maps.xlsx', sheet_name=rpt_id)
        df.columns = ['lab_eng', 'lab_kor', 'dtype', 'ifrs_ref', 'id', 'name']
        dfc = df[['lab_eng','lab_kor','id']].iloc[2:,:].reset_index(drop=True)
        dfc.lab_eng = dfc.lab_eng.str.replace(' [abstract]','',regex=False)
        dfc.lab_eng = dfc.lab_eng.str.lower()
        for k, v in typomap.items():
            dfc.lab_eng = dfc.lab_eng.str.replace(k,v)
        self.dfc = dfc
        with open('data/acnt/skeleton_trees.json') as json_file:
            skeleton_trees = json.load(json_file)
            self.skeleton_tree = skeleton_trees[rpt_id]

    @property
    def id_kr_map(self):
        return dict(zip(self.dfc.id,self.dfc.lab_kor))

    @property
    def tree_in_en(self):
        tree_in_en = deepcopy(self.skeleton_tree)
        dups = self.dfc.lab_eng.duplicated()
        for lab, dup in zip(self.dfc.lab_eng.tolist(),dups.tolist()):
            curr_path = find_path(lab, self.skeleton_tree)
            if (curr_path != None) & (not dup):
                prev_path = curr_path
            else:
                loc = tree_in_en.copy()
                for k in prev_path:
                    loc = loc[k]
                loc.append(lab)
        return tree_in_en

    @property
    def tree_in_id(self):
        str_tree = str(self.tree_in_en).replace("\'",'\"')
        str_tree = str_tree.replace('stockholder"s',"stockholder's")
        str_tree = str_tree.replace('entity"s',"entity's")
        for en, id in zip(self.dfc.lab_eng, self.dfc.id):
            str_tree = str_tree.replace(f'\"{en}\"',f'\"{id}\"',1)
        return json.loads(str_tree)

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
