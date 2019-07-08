#!/bin/bash
python manage.py cretedb
python manage.py makemigrations users

echo "Applying database migrations"
python manage.py migrate --run-syncdb

echo "Creating superuser"
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(username='${ADMIN_USER:-admin}', email='${ADMIN_EMAIL:-admin@email.invalid}', password='${ADMIN_PASSWORD:-password}',phone='+358000')" | python manage.py shell

echo "Starting server"
python manage.py runserver 0.0.0.0:8000
