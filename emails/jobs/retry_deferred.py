import logging

from django_extensions.management.jobs import HourlyJob
from mailer.models import Message

logger = logging.getLogger(__name__)

class Job(HourlyJob):
    help = "Retry deferred messages"

    def execute(self):
        count = Message.objects.retry_deferred()
        logger.info(f"moved {count} messages from deferred to queue")
