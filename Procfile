web: python manage.py migrate && gunicorn config.wsgi --bind 0.0.0.0:$PORT
worker: celery -A config worker --loglevel=info --pool=solo