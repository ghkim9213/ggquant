from ggdb.models import Corp
from math import ceil

import datetime
import json
import requests
import time

def get_bybq_range():
    today = datetime.datetime.today().date()
    today_by = today.year
    today_bq = ceil(today.month/3)
    to_bq = today_bq - 1
    if to_bq == 0:
        to_by = today_by - 1
        to_bq = 4
    else:
        to_by = today_by

    bybq_range = []
    prev_by, prev_bq = 2015, 3
    while True:
        bq = prev_bq + 1
        if bq == 5:
            by = prev_by + 1
            bq = bq - 4
        else:
            by = prev_by
        bybq_range.append((by, bq))
        if (by, bq) == (to_by, to_bq):
            break
        prev_by, prev_bq = by, bq
    return bybq_range


with open('.etc/dart_crtfc_key.txt') as f:
    ck = f.readline().strip()

bybq_range = get_bybq_range()
corp_all = Corp.objects.all()
url = 'https://opendart.fss.or.kr/api/empSttus.json'
BQ_MAP = {
    1: 11013,
    2: 11012,
    3: 11014,
    4: 11011,
}

data = []
for corp in corp_all:
    for by, bq in bybq_range:
        time.sleep(.1)
        payload = {
            'crtfc_key': ck,
            'corp_code': corp.corpCode,
            'bsns_year': by,
            'reprt_code': BQ_MAP[bq]
        }
        r = requests.get(url, payload)
        d = json.loads(r.text)
        status = d.pop('status', None)
        if status != '000':
            continue
        if status == '020':
            break
        rows = d.pop('list', None)
        n_emp_all = []
        wage_all = []
        for r in rows:
            n_emp = r.pop('sm', None)
            if n_emp == '-':
                n_emp = 0
            else:
                n_emp = int(n_emp.replace(',',''))
            n_emp_all.append(n_emp)

            wage = r.pop('fyer_salary_totamt', None)
            if wage == '-':
                wage = 0
            else:
                wage = int(wage.replace(',',''))
            wage_all.append(wage)
        new_data = {
            'corp': corp,
            'by': by,
            'bq': bq,
            'n_emp': sum(n_emp_all),
            'wage': sum(wage_all),
        }
        data.append(new_data)

    if status == '020':
        break
    if len(data) == 1000:
        break
