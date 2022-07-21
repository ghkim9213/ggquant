from django.urls import path
from .consumers import TicksConsumer , MinutesConsumer

ws_urlpatterns = [
    path('ws/ticks/', TicksConsumer.as_asgi() ),
    path('ws/minutes/', MinutesConsumer.as_asgi()),
]
