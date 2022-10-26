from django.core.management.base import BaseCommand

from utils.dataimport import DataImport
from nordigenautomation.models import Requisition


class Command(BaseCommand):
    help = "Fetch new transactions from nordigen and import"

    def handle(self, *args, **options):
        requisitions = Requisition.active.all()

        for requisition in requisitions:
            # fetch transactions for this requisition
            transactions = requisition.get_transactions()
            DataImport.import_nordigen(transactions)
