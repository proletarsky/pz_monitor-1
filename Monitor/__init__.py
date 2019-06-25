# ./__init__.py
from __future__ import absolute_import, unicode_literals
from Monitor.celery import app as celery_app

__all__ = ['celery_app']
