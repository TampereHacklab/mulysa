from django_extensions.management.jobs import DailyJob

from utils.businesslogic import BusinessLogic


class Job(DailyJob):
    help = "Queue notifications for service subscriptions that are about to expire"

    def execute(self):
        qs = BusinessLogic.find_expiring_service_subscriptions()
        BusinessLogic.notify_expiring_service_subscriptions(qs)
