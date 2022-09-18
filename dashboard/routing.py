from django.urls import path
from .consumers import StkrptArConsumer
from .consumers import StkrptFaConsumer
from .consumers import StkrptCustomArConsumer

websocket_urlpatterns = [
    path('ws/dashboard/stkrpt/ar', StkrptArConsumer.as_asgi()),
    path('ws/dashboard/stkrpt/fa', StkrptFaConsumer.as_asgi()),
    path('ws/dashboard/stkrpt/car', StkrptCustomArConsumer.as_asgi()),
]
