from django_extensions.management.jobs import MinutelyJob
from mailer.engine import send_all


class Job(MinutelyJob):
    help = "Process django-mailer queue"

    def execute(self):
        send_all()
