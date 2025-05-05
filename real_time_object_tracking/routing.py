from django.urls import path
from .consumers import TrafficCounterConsumer

websocket_urlpatterns = [
    path("ws/run_video", TrafficCounterConsumer.as_asgi()),
]