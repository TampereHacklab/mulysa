from django.core.management.base import BaseCommand

from users.models import Statistics


class Command(BaseCommand):
    help = "Collect daily statistics data"

    def handle(self, *args, **options):
        Statistics.stats.take_daily_stats()
