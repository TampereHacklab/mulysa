from django.core.management.base import BaseCommand

from utils.businesslogic import BusinessLogic

# This should be safe to run


class Command(BaseCommand):
    help = "Updates all user info"

    def handle(self, *args, **options):
        BusinessLogic.update_all_users()
