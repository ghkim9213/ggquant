# set task frequency : run tasks.py for a second
# see display/tasks.py

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ggquant.settings')

app = Celery('ggquant')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    # 'update_ticks':{
    #     'task':'dashboard.tasks.update_ticks',
    #     'schedule':1.0,
    # },
    # 'update_minutes':{
    #     'task':'dashboard.tasks.update_minutes',
    #     'schedule':1.0,
    # },
    'update_corpinfo':{
        'task':'dashboard.tasks.update_corpinfo',
        'schedule':crontab(hour=7, minute=30),
    },
    'update_accounts':{
        'task':'dashboard.tasks.update_accounts',
        'schedule':crontab(hour=5, minute=0),
    }
}

app.autodiscover_tasks()
