from .tasktools.corp import *
from .tasktools.fs import *
from .tasktools.account_ratio import *

# from asgiref.sync import async_to_sync
# from celery import shared_task
# from celery.signals import worker_ready, worker_shutdown, task_prerun
# from channels.layers import get_channel_layer
# from django.forms.models import model_to_dict

# from dashboard.initdb.createTables import *
# from dashboard.datareader import *
# from dashboard.models import Corpinfo, Accounts
# from ggquant.my_settings import ghkim

import time

# channel_layer = get_channel_layer()


# date = '20211111'
# time_reader = TimeReader(date)
# tick_reader = TickReader(date)
# minute_alarm = MinuteAlarm()
# con = pymysql.connect(db='ggquant',passwd=ghkim['passwd'])
# cur = con.cursor()
#
# @shared_task
# def update_ticks():
#     # get data
#     time_reader.ticktock()
#     res = tick_reader.ticktock(time_reader.now)
#     status, data = res['status'], res['data']
#     if res['status'] == '010':
#         # write on db
#         colnames = str(tuple(['id','datetime']+list(data['items'][0].keys()))).replace("'","`")
#         records = [tuple(i.values()) for i in data['items']]
#         sqlsyntax = f'''
#             INSERT INTO ticks {colnames}
#             VALUES (NULL,'{time_reader.now}', %s, %s, %s, %s, %s)
#         '''
#         # con = pymysql.connect(db='ggquant',passwd=ghkim['passwd'])
#         # cur = con.cursor()
#         cur.executemany(sqlsyntax,records)
#         con.commit()
#         # con.close()
#
#     # send to front
#     examples = data.copy()
#     if examples['items'] != None:
#         examples['items'] = examples['items'][:10]
#     async_to_sync(channel_layer.group_send)('ticks_ex',{'type':'send_new_data', 'text': examples})
#
# @shared_task
# def update_minutes():
#     if minute_alarm.ringring():
#         print("ringring!!")
#         res = get_minutes(minute_alarm.prev_minute)
#         status, data = res['status'], res['data']
#         if status == '010':
#             colnames = str(tuple(['id','datetime']+list(data['items'][0].keys()))).replace("'","`")
#             records = [tuple(i.values()) for i in data['items']]
#             sqlsyntax = f'''
#                 INSERT INTO minutes {colnames}
#                 VALUES (NULL,'{data['datetime']}', %s, %s, %s, %s, %s, %s, %s)
#             '''
#             # con = pymysql.connect(db='ggquant',passwd=ghkim['passwd'])
#             # cur = con.cursor()
#             cur.executemany(sqlsyntax,records)
#             con.commit()
#             # con.close()
#         else:
#             pass
#         examples = data.copy()
#         if examples['items'] != None:
#             examples['items'] = examples['items'][:10]
#         async_to_sync(channel_layer.group_send)('minutes_ex',{'type':'send_new_data','text':examples})

def update_corp():
    cm = CorpManager()
    cm.update()

def update_fs():
    ftm = FsTypeManager()
    ftm.update()

    fam = FsAccountManager()
    fam.update()
    t2 = time.time()

    odfm = OpendartFileManager()
    odfm.update()
    t3 = time.time()

    if len(odf._updated_file_all) > 0:
        for odf in odfm._updated_file_all:
            fsm = FsManager(odf)
            fsm.update()
            fsm.update_details()

        arm = AccountRatioManager()
        arm.update()
        arm.bulk_inspect()


# @worker_shutdown.connect
# def at_shutdown(sender=None,**kwargs):
#     con.close()
