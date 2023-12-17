from django_extensions.management.jobs import DailyJob

from users.models import Statistics


class Job(DailyJob):
    help = "Collect statistics"

    def execute(self):
        Statistics.objects.collect_daily_stats()
