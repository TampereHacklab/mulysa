from django.core.management.base import BaseCommand

from users.models import CustomUser, ServiceSubscription

# Caution: This does some destructive operations. Run only if you are sure.

class Command(BaseCommand):
    help = "Moves refs from user to service sub with service 2"

    def handle(self, *args, **options):
        subscriptions = ServiceSubscription.objects.all()
        for subscription in subscriptions:
            if subscription.service.id == 2:
                subscription.reference_number = None
                subscription.save()
                print(f'Cleared ref for service subscription {subscription}')

        subscriptions = ServiceSubscription.objects.all()
        for subscription in subscriptions:
            if subscription.service.id == 2:
                print(f'Handling service subscription {subscription} to ref {subscription.user.reference_number}')
                subscription.reference_number = subscription.user.reference_number
                subscription.save()
