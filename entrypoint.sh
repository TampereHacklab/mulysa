#!/bin/bash
set +x
pipenv run django-admin compilemessages

echo "Applying database migrations"
pipenv run python manage.py migrate

echo "Importing memberservices data"
pipenv run python manage.py loaddata memberservices

echo "Creating default superuser if no users defined yet"
pipenv run python manage.py initadmin

echo "Starting server"
pipenv run python -u manage.py runserver 0.0.0.0:8000 --noreload
