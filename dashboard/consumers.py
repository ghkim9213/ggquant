# generate a websocket for data to display
# from 'display/tasks.py' to 'display/index.html'

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TicksConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('ticks_ex',self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('ticks_ex',self.channel_name)

    async def send_new_data(self,event):
        new_data = event['text']
        await self.send(json.dumps(new_data))


class MinutesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('minutes_ex',self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('minutes_ex',self.channel_name)

    async def send_new_data(self,event):
        new_data = event['text']
        await self.send(json.dumps(new_data))
