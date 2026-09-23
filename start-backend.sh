#!/bin/bash
cd "$(dirname "$0")/backend"
python manage.py migrate --noinput
# The rate limits on comments and the contact form keep their counters here.
python manage.py createcachetable
echo "Starting Django backend on http://localhost:8000"
python manage.py runserver
