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
        request_type = inputs.pop('type')
        data = inputs.pop('data')

        stock_code = data.pop('stockCode', None)
        arp = ArPanel(stock_code, self.channel_name)

        ar = data.pop('ar')
        if request_type == 'ts':
            arp.get_ts_data(ar)
        elif request_type == 'dist':
            tp = data.pop('tp')
            arp.get_dist_data(ar, tp)

    def send_arp(self, event):
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
            inputs['nm']
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

        request_type = inputs.pop('type')
        data = inputs.pop('data')
        stock_code = data.pop('stockCode')
        car = CustomAr(stock_code, self.channel_name)

        # check item
        if request_type == 'checkItem':
            oc = data.pop('oc')
            acnt_nm = data.pop('nm')
            car.check_item(oc, acnt_nm)

        elif request_type == 'checkCar':
            custom_ar = data.pop('customAr')
            car.check_car(custom_ar)

        elif request_type == 'ts':
            custom_ar = data.pop('ar')
            car.get_ts_data(custom_ar)

        elif request_type == 'dist':
            custom_ar = data.pop('ar')
            tp = data.pop('tp')
            car.get_dist_data(custom_ar, tp)

    def send_car(self, event):
        self.send(event['text'])
