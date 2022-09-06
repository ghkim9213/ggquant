# generate a websocket for data to display
# from 'display/tasks.py' to 'display/index.html'

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from .tasks import *
from .models import WebsocketClient

# class StkrptArConsumer(AsyncWebsocketConsumer):
#
#     async def connect(self):
#         await self.channel_layer.group_add('stkrpt_ar', self.channel_name)
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard('stkrpt_ar', self.channel_name)
#
#     async def receive(self, text_data):
#         inputs = json.loads(text_data)
#         stock_code, oc, ar_nm = (
#             inputs['stockCode'],
#             inputs['oc'],
#             inputs['arName']
#         )
#         if oc and ar_nm:
#             await get_stkrpt_ar_data(stock_code, oc, ar_nm)
#
#     async def send_data(self, event):
#         await self.send(event['text'])


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


# class StkrptFaConsumer(AsyncWebsocketConsumer):
#
#     async def connect(self):
#         await self.channel_layer.group_add('stkrpt_fa', self.channel_name)
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard('stkrpt_fa', self.channel_name)
#
#     async def receive(self, text_data):
#         inputs = json.loads(text_data)
#         stock_code, oc, acnt_nm = (
#             inputs['stockCode'],
#             inputs['oc'],
#             inputs['faName']
#         )
#         await get_stkrpt_fa_data(stock_code, oc, acnt_nm)
#
#     async def send_data(self, event):
#         print(f"send data: {json.loads(event['text'])['fa_info']}")
#         await self.send(event['text'])


class StkrptFaConsumer(WebsocketConsumer):

    def connect(self):
        WebsocketClient.objects.create(channel_name=self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        WebsocketClient.objects.filter(channel_name=self.channel_name).delete()

    def receive(self, text_data):
        print('receive')
        inputs = json.loads(text_data)
        stock_code, oc, acnt_nm = (
            inputs['stockCode'],
            inputs['oc'],
            inputs['faName']
        )
        get_stkrpt_fa_data(stock_code, oc, acnt_nm, self.channel_name)

    def fa_data(self, event):
        print(f"send data: {json.loads(event['text'])['fa_info']}")
        self.send(event['text'])
