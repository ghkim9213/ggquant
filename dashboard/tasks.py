from .contents.ar_panel import *
from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from celery.utils.log import get_task_logger
from channels.layers import get_channel_layer
from ggdb.models import *

import datetime

# today = datetime.datetime.today().date()

# @shared_task
@sync_to_async
def get_stkrpt_ar_data(stock_code, oc, ar_nm):
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
    async_to_sync(channel_layer.group_send)('stkrpt_ar', {
            'type': 'send_data',
            'text': data
        }
    )
