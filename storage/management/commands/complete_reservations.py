from django.core.management.base import BaseCommand
from storage.utils.expire_pending_reservations import expire_pending_reservations


class Command(BaseCommand):
    help = "Update reservation statuses"

    def handle(self, *args, **kwargs):
        expire_pending_reservations()
