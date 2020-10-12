#!/bin/bash
set +x
pipenv run django-admin compilemessages

echo "Applying database migrations"
pipenv run python manage.py migrate

echo "collecting static files"
pipenv run python manage.py collectstatic --clear --no-input

echo "Importing initial memberservices data if none exists"
pipenv run python manage.py initmemberservices

echo "Creating default superuser if no users defined yet"
pipenv run python manage.py initadmin

echo "Starting server"
pipenv run gunicorn drfx.wsgi:application --bind 0.0.0.0:8000