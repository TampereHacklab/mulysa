import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import CustomUser

from drfx import config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete all users that have been marked for deletion for more than the cutoff setting"

    def handle(self, *args, **options):
        # some safety margin
        dt = timezone.now() - timezone.timedelta(days=config.USER_DELETION_DAYS)

        logger.info(
            f" Search for users that have been marked for deletion for over {config.USER_DELETION_DAYS} days"
        )

        users = CustomUser.objects.filter(
            marked_for_deletion_on__isnull=False, marked_for_deletion_on__lt=dt
        )

        for user in users:
            logger.info(
                f" Deleting User {user} as it has been marked for deletion over {config.USER_DELETION_DAYS} days"
            )
            user.delete()
