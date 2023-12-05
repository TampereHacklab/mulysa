from django.core.management.base import BaseCommand

from users.models import (
    Statistics,
    CustomUser,
    MembershipApplication,
    ServiceSubscription,
    UsersLog,
    CustomInvoice,
)


class Command(BaseCommand):
    help = "Collect daily statistics data"

    def handle(self, *args, **options):

        s = Statistics()
        s.total_users = CustomUser.objects.all().count()
        s.active_users = CustomUser.objects.filter(is_active=1).count()
        s.open_member_applications = MembershipApplication.objects.all().count()

        s.save()



