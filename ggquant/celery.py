import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ggquant.settings')

app = Celery('ggquant')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'batchs': {
        'task': 'ggdb.tasks.batchs',
        'schedule': crontab(minute=0, hour=5),
        },
    'test': {
        'task': 'ggdb.tasks.test',
        'schedule': 30.0,
     },
}
