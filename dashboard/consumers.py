# generate a websocket for data to display
# from 'display/tasks.py' to 'display/index.html'

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from .tasks import *
from .models import WebsocketClient

class StkrptArConsumer(WebsocketConsumer):

    def connect(self):
        WebsocketClient.objects.create(channel_name=self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        WebsocketClient.objects.filter(channel_name=self.channel_name).delete()

    def receive(self, text_data):
        inputs = json.loads(text_data)
        stock_code, oc, ar_nm = (
            inputs['stockCode'],
            inputs['oc'],
            inputs['arName']
        )
        if oc and ar_nm:
            get_stkrpt_ar_data(stock_code, oc, ar_nm, self.channel_name)

    def ar_data(self, event):
        self.send(event['text'])


class StkrptFaConsumer(WebsocketConsumer):

    def connect(self):
        WebsocketClient.objects.create(channel_name=self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        WebsocketClient.objects.filter(channel_name=self.channel_name).delete()

    def receive(self, text_data):
        inputs = json.loads(text_data)
        stock_code, oc, acnt_nm = (
            inputs['stockCode'],
            inputs['oc'],
            inputs['faName']
        )
        get_stkrpt_fa_data(stock_code, oc, acnt_nm, self.channel_name)

    def fa_data(self, event):
        self.send(event['text'])
