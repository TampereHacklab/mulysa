from django.core.management.base import BaseCommand
from users.models import CustomUser, BankTransaction, UsersLog, ServiceSubscription
from utils.businesslogic import BusinessLogic

# Caution: This does some destructive operations. Run only if you are sure.

class Command(BaseCommand):
    help = "Deletes all service subscription state and recalculates them from bank ledger"

    def handle(self, *args, **options):
        users = CustomUser.objects.all()

        for user in users:
            print(f" --- User {user}")
            self.reset_user(user)

        print('\nUsers reset - now playing back transactions.\n')

        transactions = BankTransaction.objects.filter(has_been_used=False).order_by('date')
        for transaction in transactions:
            print(f'Unused transaction: {transaction}')
            BusinessLogic.new_transaction(transaction)

        print('\nAll done!')

    def reset_user(self, user):
        logentries = UsersLog.objects.filter(user=user)

        for entry in logentries:
            print(f'Deleting log entry {entry}')

        logentries.delete()

        subscriptions = ServiceSubscription.objects.filter(user=user)

        for subscription in subscriptions:
            print(f'Resetting service subscription {subscription} which is {subscription.state}')
            subscription.state = ServiceSubscription.OVERDUE
            subscription.paid_until = None
            subscription.last_payment = None
            subscription.save()

        transactions = BankTransaction.objects.filter(user=user)
        for transaction in transactions:
            print(f'Resetting user transaction {transaction}')
            transaction.has_been_used = False
            transaction.user = None
            transaction.save()

        user.log("User's payment history begins")
