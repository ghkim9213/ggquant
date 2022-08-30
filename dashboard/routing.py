from django.urls import path
from .consumers import StkrptArConsumer

websocket_urlpatterns = [
    path('ws/dashboard/stkrpt/ar/<stock_code>/', StkrptArConsumer.as_asgi()),
]
