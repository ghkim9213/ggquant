from django.urls import path
from .consumers import StkrptArConsumer, StkrptFaConsumer

websocket_urlpatterns = [
    path('ws/dashboard/stkrpt/ar', StkrptArConsumer.as_asgi()),
    path('ws/dashboard/stkrpt/fa', StkrptFaConsumer.as_asgi()),
]
