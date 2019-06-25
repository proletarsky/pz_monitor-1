# machines/celery.py

from __future__ import absolute_import
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Monitor.settings')

app = Celery('Monitor')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def test_task(self):
    print(r'Request: {0!r}'.format(self.request))
