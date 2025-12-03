from django.core.management.base import BaseCommand
from storage.utils.complete_reservations import complete_finished_reservations


class Command(BaseCommand):
    help = "Update reservation statuses"

    def handle(self, *args, **kwargs):
        complete_finished_reservations()
