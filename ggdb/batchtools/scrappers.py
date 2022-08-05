from bs4 import BeautifulSoup
from ggquant.my_settings import dart_crtfc_key
from io import BytesIO

import json, os, requests, zipfile, xmltodict, zipfile
import numpy as np
import pandas as pd


# scrap filename list from openDART
def scrap_opendart_filename_all():
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/list.do'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atags = soup.find('table','tb01').find_all('a')
    get_filename = lambda a: a['onclick'][a['onclick'].find('(')+1:a['onclick'].find(')')].split(', ')[-1][1:-1]
    return [get_filename(a) for a in atags]

# download openDART file
def download_opendart_file(filename):
    print(f"...downloading {filename}")
    download_url = 'https://opendart.fss.or.kr/cmm/downloadFnlttZip.do'
    download_payload = {'fl_nm':filename}
    download_headers = {
        'Referer':'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do',
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    }
    r = requests.get(download_url,download_payload,headers=download_headers)
    f = zipfile.ZipFile(BytesIO(r.content))
    return f


# scrap corp list from KIND
def scrap_kind_corp_all(marketType):
    print(f"downloading {marketType} data for the model 'Corp' from KIND...")
    url = 'https://kind.krx.co.kr/corpgeneral/corpList.do'
    if marketType == 'KOSPI':
        marketType_payload = 'stockMkt'
    elif marketType == 'KOSDAQ':
        marketType_payload = 'kosdaqMkt'
    payload = {
        'method':'download',
        'pageIndex':'1',
        'currentPageSize':'10000',
        'marketType':marketType_payload,
    }
    res = requests.post(url,payload)
    table = pd.read_html(res.content)[0]
    table.columns = ['stock_name','stock_code','industry','product','listed_at','fye','ceo','homepage','district']
    table['market'] = marketType
    table['stock_code'] = table['stock_code'].astype(str).str.zfill(6)
    table['fye'] = table['fye'].str[:-1].astype(int)
    table = table.replace(np.nan, None)
    print('...complete')
    return table.to_dict(orient='records') #json.loads(table.set_index('stock_code').to_json(force_ascii=False,orient='index'))


def scrap_opendart_corp_all():
    print("downloading data for the model 'Corp' from DART")
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    r = requests.get(url,{'crtfc_key':dart_crtfc_key})
    f = BytesIO(r.content)
    zf = zipfile.ZipFile(f)
    xml = zf.read(zf.namelist()[0]).decode('utf-8')
    data = xmltodict.parse(xml)['result']['list']
    print("...complete")
    return [dict(d) for d in data]
