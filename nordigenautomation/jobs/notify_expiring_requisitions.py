from datetime import timedelta

from django_extensions.management.jobs import DailyJob
from django.utils import timezone
from django.core.mail import send_mail

from drfx import settings
from ..models import Requisition


class Job(DailyJob):
    help = "Send notifications if there are requisitions that are about to expire"

    def execute(self):
        # about to end in 14 days
        in_fourteen_days = timezone.now() + timedelta(days=14)
        for r in Requisition.active.filter(valid_until__lte=in_fourteen_days):
            print("sending alert")
            send_mail(
                f"[{settings.SITENAME}] Requisition about to expire",
                f"Please update the requisition for config: {r.config.id}. It is valid until: {r.valid_until}",
                settings.NOREPLY_FROM_ADDRESS,
                [settings.MEMBERSHIP_APPLICATION_NOTIFY_ADDRESS],
                fail_silently=False,
            )
