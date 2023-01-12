from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create initial admin user if no users exists"

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.count() == 0:
            User.objects.create_superuser(
                first_name="Admin",
                last_name="User",
                email="admin@email.invalid",
                password="rootme",
                phone="+358000",
            )
            print("Created initial admin user")
        else:
            print("Skipping admin user initialization, database already has users")
