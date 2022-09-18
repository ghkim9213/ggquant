from .contents.ar_panel import *
from .contents.custom_ar import *
from .contents.fa_ts import *
from .models import WebsocketClient
from channels.generic.websocket import WebsocketConsumer

import json


class StkrptArConsumer(WebsocketConsumer):

    def connect(self):
        WebsocketClient.objects.create(channel_name=self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        WebsocketClient.objects.filter(channel_name=self.channel_name).delete()

    def receive(self, text_data):
        inputs = json.loads(text_data)
        request_type = inputs.pop('requestType')

        stock_code = inputs.pop('stockCode', None)
        oc = inputs.pop('oc', None)
        ar_nm = inputs.pop('arName', None)
        tp = inputs.pop('tp', None)

        arp = ArPanel(ar_nm, oc, stock_code, self.channel_name)
        if request_type == 'static':
            arp.generate_static_data()
        elif request_type == 'dynamic':
            arp.generate_dynamic_data(tp)

    def ar_static(self, event):
        self.send(event['text'])

    def ar_dynamic(self, event):
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
        fa_ts = FaTs(acnt_nm, oc, stock_code, self.channel_name)
        fa_ts.generate_data()
        # get_stkrpt_fa_data(stock_code, oc, acnt_nm, self.channel_name)

    def fa_data(self, event):
        self.send(event['text'])



class StkrptCustomArConsumer(WebsocketConsumer):

    def connect(self):
        WebsocketClient.objects.create(channel_name=self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        WebsocketClient.objects.filter(channel_name=self.channel_name).delete()

    def receive(self, text_data):
        inputs = json.loads(text_data)

        request_type = inputs.pop('requestType')
        stock_code = inputs.pop('stockCode')
        car = CustomAr(stock_code, self.channel_name)

        # check item
        if request_type == 'checkItem':
            oc = inputs.pop('oc')
            acnt_nm = inputs.pop('itemName')
            car.check_item(oc, acnt_nm)
        elif request_type == 'static':
            ar_syntax = inputs.pop('arSyntax')

            pass
        elif request_type == 'dynamic':
            pass

    def car_check_item(self, event):
        self.send(event['text'])
