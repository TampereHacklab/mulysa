from django.core.management.base import BaseCommand

from drfx import config
from users.models import ServiceSubscription

from utils import referencenumber

# Caution: This does some destructive operations. Run only if you are sure.


class Command(BaseCommand):
    help = "Generates missing reference numbers for services that don't have them"

    def handle(self, *args, **options):
        subscriptions = ServiceSubscription.objects.all()
        for subscription in subscriptions:
            if not subscription.reference_number:
                print(f"Generating ref for service subscription {subscription}")
                subscription.reference_number = referencenumber.generate(
                    config.SERVICE_INVOICE_REFERENCE_BASE + subscription.id
                )
                subscription.save()
