from .contents.ar_panel import *
from .contents.fa_ts import *

from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from channels.layers import get_channel_layer
from ggdb.models import *

import datetime
import json

# today = datetime.datetime.today().date()
# channel_layer = get_channel_layer()

# @sync_to_async
def get_stkrpt_ar_data(stock_code, oc, ar_nm, channel_name):
    try:
        arp = ARPanel(ar_nm, oc, stock_code)
        table = arp.get_table().to_json(orient='records')
        fig_all = {}
        alpha_all = [0, .01, .05]
        for alpha in alpha_all:
            arp.update_graph_data(alpha=alpha)
            arp.update_layout()
            arp.update_traces()
            arp.update_frames()
            arp.update_sliders()
            fig_name = f"pct{int((1-alpha)*100)}"
            fig_all[fig_name] = arp.get_figure().to_json()
        data = json.dumps({
            'figures': fig_all,
            'table': table,
        })
    except KeyError:
        data = json.dumps(None)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(channel_name, {
            'type': 'ar.data',
            'text': data
        }
    )


# @sync_to_async
# def get_stkrpt_fa_data(stock_code, oc, acnt_nm):
#     try:
#         print(f"task input {acnt_nm}")
#         fa_ts = FaTs(acnt_nm, oc, stock_code)
#         fa_ts.update_fa_info()
#         fa_ts.update_graph_data()
#         print(f"task output for {acnt_nm}: {fa_ts._fa_info}")
#         data = fa_ts.get_data()
#     except KeyError:
#         data = json.dumps(None)
#
#
#     # channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)('stkrpt_fa', {
#             'type': 'send_data',
#             'text': data
#         }
#     )

# @sync_to_async
def get_stkrpt_fa_data(stock_code, oc, acnt_nm, channel_name):
    try:
        print(f"task input {acnt_nm}")
        fa_ts = FaTs(acnt_nm, oc, stock_code)
        fa_ts.update_fa_info()
        fa_ts.update_graph_data()
        print(f"task output for {acnt_nm}: {fa_ts._fa_info}")
        data = fa_ts.get_data()
    except KeyError:
        data = json.dumps(None)


    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(channel_name, {
            'type': 'fa.data',
            'text': data
        }
    )
