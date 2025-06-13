# medipt_backend_backend/medipt_backend/celery.py

from __future__ import absolute_import, unicode_literals
import os
import ssl
from celery import Celery
from django.conf import settings
from urllib.parse import urlparse

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medipt.settings.production')

app = Celery('medipt')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

broker_url = app.conf.broker_url

result_backend = app.conf.result_backend


if urlparse(broker_url).scheme == 'rediss':
    ssl_opts = {'ssl_cert_reqs': ssl.CERT_NONE}
    app.conf.broker_use_ssl = ssl_opts
    app.conf.redis_backend_use_ssl = ssl_opts

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
