from .contents.ar_panel import *
from .contents.fa_ts import *

from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from channels.layers import get_channel_layer
from ggdb.models import *

import json

def get_stkrpt_ar_data(stock_code, oc, ar_nm, channel_name):
    try:
        arp = ArPanel(ar_nm, oc, stock_code)
        arp.update_table_data()
        arp.update_graph_data()
        data = arp.get_data()
    except KeyError:
        data = json.dumps(None)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(channel_name, {
            'type': 'ar.data',
            'text': data
        }
    )

def get_stkrpt_fa_data(stock_code, oc, acnt_nm, channel_name):
    try:
        fa_ts = FaTs(acnt_nm, oc, stock_code)
        fa_ts.update_fa_info()
        fa_ts.update_graph_data()
        data = fa_ts.get_data()
    except KeyError:
        data = json.dumps(None)


    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(channel_name, {
            'type': 'fa.data',
            'text': data
        }
    )
