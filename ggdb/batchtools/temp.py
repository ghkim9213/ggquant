from collections import Counter
from ggdb.models import *

import json


class  AccountRatioCrossSectionManager:
    def __init__(self):
        self.ar_all = AccountRatio.objects.all()
        self.filepath = lambda oc, market: f"ggdb/temp/dashboard/account_ratio/cross_section/{oc}_{market}.json"

    def table_header(self, oc, market):
        with open(self.filepath(oc, market)) as f:
            row = json.load(f)[0]
        header_all = [AccountRatio.objects.get(name=x) for x in list(row.keys())[3:]]
        lk_all = [h.labelKor for h in header_all]
        div_counter = Counter([h.div for h in header_all])
        table_header0 = f'''
            <tr>
                <th rowspan="2">종목코드</th>
                <th rowspan="2">종목명</th>
                <th rowspan="2">결산기준일</th>
                <th colspan="{div_counter['안정성']}">안정성</th>
                <th colspan="{div_counter['수익성']}">수익성</th>
                <th colspan="{div_counter['성장성 및 활동성']}">성장성 및 활동성</th>
            </tr>
        '''
        table_header1 = ""
        for lk in lk_all:
            table_header1 += f"<th>{lk}</th>"
        table_header1 = f"<tr>{table_header1}</tr>"
        return table_header0 + table_header1

    def table_rows(self, oc, market):
        with open(self.filepath(oc, market)) as f:
            return json.load(f)

    def update(self):
        print("updating tempfiles: account ratio cross section...")
        for oc in ['OFS', 'CFS']:
            df_all = pd.concat([ar.recent_values(oc) for ar in self.ar_all], axis=1).round(4)
            for market in ['KOSPI', 'KOSDAQ']:
                print(f"...writing {self.filepath(oc, market)}")
                with open(self.filepath(oc, market), 'w') as f:
                    json.dump(
                        json.loads(df_all.loc[market].reset_index().sort_values(['stock_code','fqe'],ascending=[True,False]).to_json(orient='records')),
                        f
                    )
        print("...complete!")
