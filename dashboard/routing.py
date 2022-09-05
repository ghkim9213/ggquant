from django.urls import path
from .consumers import StkrptArConsumer, StkrptFaConsumer

websocket_urlpatterns = [
    path('ws/dashboard/stkrpt/ar/<stock_code>', StkrptArConsumer.as_asgi()),
    path('ws/dashboard/stkrpt/fa/<fa_nm>/<stock_code>', StkrptFaConsumer.as_asgi()),
]
