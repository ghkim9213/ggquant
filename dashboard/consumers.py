# generate a websocket for data to display
# from 'display/tasks.py' to 'display/index.html'

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import *

class StkrptArConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add('stkrpt_ar', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('stkrpt_ar', self.channel_name)

    async def receive(self, text_data):
        inputs = json.loads(text_data)
        stock_code, oc, ar_nm = (
            inputs['stockCode'],
            inputs['oc'],
            inputs['arName']
        )
        if oc and ar_nm:
            print('consumer has received data')
            await get_stkrpt_ar_data(stock_code, oc, ar_nm)

    async def send_data(self, event):
        print('consumer sending data')
        await self.send(event['text'])
