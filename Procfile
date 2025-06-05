web: gunicorn medipt.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A medipt worker --loglevel=info