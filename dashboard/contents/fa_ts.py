from .data.fa import FaSeries
from .data.tools import *
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
from ggdb.models import Corp, FsAccount, FsDetail

import json
import pandas as pd

class FaTs:
    def __init__(self, acnt_nm, oc, stock_code, channel_name):
        self.fas = FaSeries(acnt_nm=acnt_nm, oc=oc)
        self.stock_code = stock_code
        self.channel_layer = get_channel_layer()
        self.channel_name = channel_name

    def generate_data(self):
        fas_info = json.dumps({
            'oc': self.fas.oc,
            'nm': self.fas.acnt_nm,
            'lk': self.fas.label_kor,
            'path': self.fas.path,
        })
        ts = self.fas.time_series(self.stock_code)
        if len(ts) > 0:
            tmin = ts.fqe.min()
            tmax = ts.fqe.max()
            ts = fill_tgap(ts)
            ts['growth'] = (ts.value / ts.value.shift(1) - 1) * 100

            chart_data = {
                't': ts.fqe.to_json(orient='records'),
                'y_val': ts.value.to_json(orient='records'),
                'y_growth': ts.growth.to_json(orient='records'),
            }
        else:
            chart_data = json.dumps(None)

        data = json.dumps({
            'fas_info': fas_info,
            'chart_data': chart_data,
        })

        async_to_sync(self.channel_layer.send)(self.channel_name, {
            'type': 'fa.data',
            'text': data,
        })
