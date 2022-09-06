from django.db import models

# Create your models here.

# from ggdb.models import *

class WebsocketClient(models.Model):
    channel_name = models.CharField(max_length=256)
