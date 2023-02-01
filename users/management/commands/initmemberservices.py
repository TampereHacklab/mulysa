from django.core.management.base import BaseCommand
from django.core.management import call_command

from users.models import MemberService


class Command(BaseCommand):
    help = "Create initial memberservices if no memberservices exist"

    def handle(self, *args, **options):

        if MemberService.objects.count() == 0:
            print("Initializing initial memberservices")
            call_command("loaddata", "memberservices")
        else:
            print("Memberservices already initialized")
