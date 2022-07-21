from asgiref.sync import async_to_sync
from celery import shared_task
from celery.signals import worker_ready, worker_shutdown, task_prerun
from channels.layers import get_channel_layer
from django.forms.models import model_to_dict

from dashboard.initdb.createTables import *
from dashboard.datareader import *
from dashboard.models import Corpinfo, Accounts
from ggquant.my_settings import ghkim

import time

channel_layer = get_channel_layer()


date = '20211111'
time_reader = TimeReader(date)
tick_reader = TickReader(date)
minute_alarm = MinuteAlarm()
con = pymysql.connect(db='ggquant',passwd=ghkim['passwd'])
cur = con.cursor()

@shared_task
def update_ticks():
    # get data
    time_reader.ticktock()
    res = tick_reader.ticktock(time_reader.now)
    status, data = res['status'], res['data']
    if res['status'] == '010':
        # write on db
        colnames = str(tuple(['id','datetime']+list(data['items'][0].keys()))).replace("'","`")
        records = [tuple(i.values()) for i in data['items']]
        sqlsyntax = f'''
            INSERT INTO ticks {colnames}
            VALUES (NULL,'{time_reader.now}', %s, %s, %s, %s, %s)
        '''
        # con = pymysql.connect(db='ggquant',passwd=ghkim['passwd'])
        # cur = con.cursor()
        cur.executemany(sqlsyntax,records)
        con.commit()
        # con.close()

    # send to front
    examples = data.copy()
    if examples['items'] != None:
        examples['items'] = examples['items'][:10]
    async_to_sync(channel_layer.group_send)('ticks_ex',{'type':'send_new_data', 'text': examples})

@shared_task
def update_minutes():
    if minute_alarm.ringring():
        print("ringring!!")
        res = get_minutes(minute_alarm.prev_minute)
        status, data = res['status'], res['data']
        if status == '010':
            colnames = str(tuple(['id','datetime']+list(data['items'][0].keys()))).replace("'","`")
            records = [tuple(i.values()) for i in data['items']]
            sqlsyntax = f'''
                INSERT INTO minutes {colnames}
                VALUES (NULL,'{data['datetime']}', %s, %s, %s, %s, %s, %s, %s)
            '''
            # con = pymysql.connect(db='ggquant',passwd=ghkim['passwd'])
            # cur = con.cursor()
            cur.executemany(sqlsyntax,records)
            con.commit()
            # con.close()
        else:
            pass
        examples = data.copy()
        if examples['items'] != None:
            examples['items'] = examples['items'][:10]
        async_to_sync(channel_layer.group_send)('minutes_ex',{'type':'send_new_data','text':examples})

# @shared_task
def update_corpinfo():
    new_data = CorpinfoToday().get_corp_info()

    # delisted
    new_stocks = [c['stock_code'] for c in new_data]
    old_data = Corpinfo.objects.all()
    old_stocks = [c.stock_code for c in old_data]
    delisted = [c for c in old_stocks if not c in new_stocks]
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    for d in delisted:
        obj = Corpinfo.objects.get(stock_code=d)
        obj.delisted_at = today
        obj.save()

    # new listed
    for d in new_data:
        obj, created = Corpinfo.objects.get_or_create(stock_code=d['stock_code'])
        if created:
            obj.corp_code = d['corp_code']
            obj.corp_name = d['corp_name']
            obj.ind = d['ind']
            obj.product = d['product']
            obj.ceo = d['ceo']
            obj.homepage = d['homepage']
            obj.district = d['district']
            obj.stock_code = d['stock_code']
            obj.market = d['market']
            obj.fye = d['fye']
            obj.listed_at = d['listed_at']
            obj.save()
        else:
            dobj = model_to_dict(obj)
            dobj.pop('id')
            dobj.pop('delisted_at')
            if d == dobj: # if no update, pass
                pass
            else: # if update, update
                obj.corp_code = d['corp_code']
                obj.corp_name = d['corp_name']
                obj.ind = d['ind']
                obj.product = d['product']
                obj.ceo = d['ceo']
                obj.homepage = d['homepage']
                obj.district = d['district']
                obj.stock_code = d['stock_code']
                obj.market = d['market']
                obj.fye = d['fye']
                obj.listed_at = d['listed_at']
                obj.save()

# @shared_task
def update_accounts():
    cr_ord = [
    'rpt_id', 'stock_code', 'rpt_nm',
    'bybq', 'rpt_date', 'acnt_id',
    'is_standard', 'acnt_nm_kr', 'currency',
    'value', 'created_at', 'last_update'
    ]
    ud_ord = [
    'rpt_id', 'stock_code', 'rpt_nm',
    'bybq', 'rpt_date', 'acnt_id',
    'is_standard', 'acnt_nm_kr', 'currency',
    'value', 'new_value', 'created_at',
    'updated_at'
    ]
    acnt_today = AccountToday()
    if acnt_today.zf_nms_download != []:
        for zf_nm in acnt_today.zf_nms_download:
            data = acnt_today.get_data(zf_nm)
            cr_today = []
            ud_today = []
            print('collecting the updates...')
            t0 = time.time()
            for d in data:
                t1 = time.time()
                try:
                    obj = Accounts.objects.get(
                        stock_code = d['stock_code'],
                        rpt_id = d['rpt_id'],
                        bybq = d['bybq'],
                        rpt_date = d['rpt_date'],
                        acnt_id = d['acnt_id']
                    )
                    if obj.value != d['value']:
                        ud = model_to_dict(obj)
                        ud['updated_at'] = ud.pop('last_update')
                        ud['new_value'] = d['value']
                        ud['rpt_date'] = str(ud['rpt_date'])
                        if ud['created_at'] != None:
                            ud['created_at'] = str(ud['created_at'])
                        ud['updated_at'] = str(ud['updated_at'])
                        ud_today.append({k:ud[k] for k in ud_ord})
                        obj.value = d['value']
                        obj.last_update = d['last_update']
                        obj.save() # takes .1~.2 sec for a row
                except Accounts.DoesNotExist:
                    d['created_at'] = d['last_update']
                    cr_today.append({k:d[k] for k in cr_ord}) # takes about 1ms for a row

            print(f'{len(cr_today)} creations and {len(ud_today)} updates occur for {zf_nm}')
            print('...complete')

            print('writing the changes on db...')
            cur.executemany(f'''
                INSERT INTO accounts
                {str(tuple(['id'] + cr_ord)).replace("'","`")}
                VALUES (
                    NULL, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s
                )
            ''', [tuple(cr.values()) for cr in cr_today])
            cur.executemany(f'''
                INSERT INTO accounts_ud
                {str(tuple(['id'] + ud_ord)).replace("'","`")}
                VALUES (
                    NULL, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                )
            ''', [tuple(ud.values()) for ud in ud_today])
            con.commit()
            print('...complete')
        acnt_today.save_last_update()
    else:
        print('no update in accounts today')


def update_accounts_manual(zf_nm):
    cr_ord = [
        'rpt_id', 'stock_code', 'rpt_nm',
        'bybq', 'rpt_date', 'acnt_id',
        'is_standard', 'acnt_nm_kr', 'currency',
        'value', 'created_at', 'last_update'
    ]
    ud_ord = [
        'rpt_id', 'stock_code', 'rpt_nm',
        'bybq', 'rpt_date', 'acnt_id',
        'is_standard', 'acnt_nm_kr', 'currency',
        'value', 'new_value', 'created_at',
        'updated_at'
    ]
    acnt_today = AccountToday()
    data = acnt_today.get_data(zf_nm)
    cr_today = []
    ud_today = []
    print('collecting the updates...')
    t0 = time.time()
    for d in data:
        t1 = time.time()
        try:
            obj = Accounts.objects.get(
                stock_code = d['stock_code'],
                rpt_id = d['rpt_id'],
                bybq = d['bybq'],
                rpt_date = d['rpt_date'],
                acnt_id = d['acnt_id']
            )
            if obj.value != d['value']:
                ud = model_to_dict(obj)
                ud['updated_at'] = ud.pop('last_update')
                ud['new_value'] = d['value']
                ud['rpt_date'] = str(ud['rpt_date'])
                if ud['created_at'] != None:
                    ud['created_at'] = str(ud['created_at'])
                ud['updated_at'] = str(ud['updated_at'])
                ud_today.append({k:ud[k] for k in ud_ord})
                obj.value = d['value']
                obj.last_update = d['last_update']
                obj.save() # takes .1~.2 sec for a row
        except Accounts.DoesNotExist:
            d['created_at'] = d['last_update']
            cr_today.append({k:d[k] for k in cr_ord}) # takes about 1ms for a row

    print(f'{len(cr_today)} creations and {len(ud_today)} updates occur for {zf_nm}')
    print('...complete')

    print('writing the changes on db...')
    cur.executemany(f'''
        INSERT INTO accounts
        {str(tuple(['id'] + cr_ord)).replace("'","`")}
        VALUES (
            NULL, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s
        )
    ''', [tuple(cr.values()) for cr in cr_today])
    cur.executemany(f'''
        INSERT INTO accounts_ud
        {str(tuple(['id'] + ud_ord)).replace("'","`")}
        VALUES (
            NULL, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s
        )
    ''', [tuple(ud.values()) for ud in ud_today])
    con.commit()
    print('...complete')


@worker_shutdown.connect
def at_shutdown(sender=None,**kwargs):
    con.close()
