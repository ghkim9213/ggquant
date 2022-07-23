from copy import deepcopy
from dashboard.models import Corp, CorpHistory
from io import BytesIO
from ggquant.my_settings import dart_crtfc_key

import datetime, requests, xmltodict, zipfile
import numpy as np
import pandas as pd


class CorpToday:


    def __init__(self):
        self.kind = get_kind('KOSPI') + get_kind('KOSDAQ')
        self.dart = get_dart()

    def get_data(self):
        data = deepcopy(self.kind)
        dart = deepcopy(self.dart)
        sc2cc_map = {x['stock_code']: x['corp_code'] for x in dart if x['stock_code'] != None}
        for d in data:
            d['corp_code'] = sc2cc_map.pop(d['stock_code'], None)
        return data

def get_kind(marketType):
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


def get_dart():
    print("downloading data for the model 'Corp' from DART")
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    r = requests.get(url,{'crtfc_key':dart_crtfc_key})
    f = BytesIO(r.content)
    zf = zipfile.ZipFile(f)
    xml = zf.read(zf.namelist()[0]).decode('utf-8')
    data = xmltodict.parse(xml)['result']['list']
    print("...complete")
    return [dict(d) for d in data]



class CorpManager:

    def __init__(self):
        self.ct = CorpToday()

    def update(self):
        # download data
        new_data = sorted(self.ct.get_data(), key=lambda x: x['listed_at'])
        new_data.reverse()
        for d in new_data:
            d['stockCode'] = d.pop('stock_code')
            d['corpCode'] = d.pop('corp_code')
            d['corpName'] = d.pop('stock_name')
            d['listedAt'] = d.pop('listed_at')

        # update
        if Corp.objects.all().exists():
            corp_all = Corp.objects.filter(delistedAt__isnull=True)
            stock_code_all = corp_all.values_list('stockCode',flat=True)
            new_corp_all = []
            new_history_all = []

            # detect changes and update
            for d in new_data:
                if d['stockCode'] in stock_code_all:
                    obj = corp_all.get(stockCode=d['stockCode'])
                    for k, v in d.items():
                        prev, curr = getattr(obj, k), v
                        if k == 'listedAt':
                            curr = datetime.datetime.strptime(curr, '%Y-%m-%d').date()
                        if prev != curr:
                            new_history_all.append(
                                CorpHistory(
                                    corp = obj,
                                    changeIn = k,
                                    prevValue = prev,
                                )
                            )
                            setattr(obj, k, curr)
                            obj.save()
                # collect new corps
                else:
                    new_corp_all.append(Corp(**d))

            # save new corps
            if len(new_corp_all) > 0:
                Corp.objects.bulk_create(new_corp_all)
            else:
                print('no new corp')

            # save history of changes in corp information
            if len(new_history_all) > 0:
                CorpHistory.objects.bulk_create(new_history_all)
            else:
                print('no new history')

            # detect delisted corps
            delisted_corp_all = []
            new_stock_code_all = [d['stockCode'] for d in new_data]
            delisted_stock_code_all = [x for x in stock_code_all if x not in new_stock_code_all]
            for sc in delisted_stock_code_all:
                obj = corp_all.get(stockCode=sc)
                obj.delistedAt = datetime.datetime.today().date()
                delisted_corp_all.append(obj)

            # save the delisted corps
            if len(delisted_corp_all) > 0:
                Corp.objects.bulk_update(delisted_corp_all,['delistedAt'])
            else:
                print('no delisted')

        # first rows for the model Corp
        else:
            corp_all = [Corp(**d) for d in new_data]
            Corp.objects.bulk_create(corp_all)
