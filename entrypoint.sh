#!/bin/bash
set +x
pipenv run django-admin compilemessages
pipenv run python manage.py makemigrations

echo "Applying database migrations"
pipenv run python manage.py migrate

echo "Creating superuser"
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(first_name='Admin', last_name='User', email='${ADMIN_EMAIL:-admin@email.invalid}', password='${ADMIN_PASSWORD:-password}',phone='+358000')" | pipenv run python manage.py shell

echo "Starting server"
pipenv run python -u manage.py runserver 0.0.0.0:8000 --noreload

