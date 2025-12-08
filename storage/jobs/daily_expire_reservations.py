from django_extensions.management.jobs import DailyJob
from storage.utils.expire_pending_reservations import expire_pending_reservations
from storage.utils.complete_reservations import complete_finished_reservations


class Job(DailyJob):
    help = "Expire unpaid reservations and complete finished reservations"

    def execute(self):
        expire_pending_reservations()
        complete_finished_reservations()
