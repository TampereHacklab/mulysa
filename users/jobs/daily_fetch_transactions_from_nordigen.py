from django_extensions.management.jobs import DailyJob

from utils.dataimport import DataImport
from nordigenautomation.models import Requisition


class Job(DailyJob):
    help = "Fetch transactions from nordigen"

    def execute(self):
        requisitions = Requisition.active.all()

        for requisition in requisitions:
            # fetch transactions for this requisition
            transactions = requisition.get_transactions()
            DataImport.import_nordigen(transactions)
