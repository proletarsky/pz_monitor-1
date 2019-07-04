# machines/celery.py

from __future__ import absolute_import
import os, sys, django
from celery import Celery
from celery._state import _set_current_app
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Monitor.settings')

app = Celery('Monitor')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

#added 19-07-04
# _set_current_app(app)
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../machines')))
# django.setup()


@app.task(bind=True)
def test_task(self):
    print(r'Request: {0!r}'.format(self.request))
