from django.core.management.base import BaseCommand

from users.models import BankTransaction

from utils.businesslogic import BusinessLogic

# Caution: This does some destructive operations. Run only if you are sure.

class Command(BaseCommand):
    help = "Recalculates all user payments from bank ledger"

    def handle(self, *args, **options):
        transactions = BankTransaction.objects.filter(has_been_used=False).order_by('date')
        for transaction in transactions:
            print(f'Unused transaction: {transaction}')
            BusinessLogic.new_transaction(transaction)

        print('Updating ALL users..')

        BusinessLogic.update_all_users()

        print('\nAll done!')
