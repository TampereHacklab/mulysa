from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from drfx import config

from ..models.storage_unit import StorageUnit
from ..models.storage_reservation import StorageReservation


@login_required
def reservation_table(request):
    units = StorageUnit.objects.all()
    reservations = StorageReservation.objects.filter(user=request.user)

    return render(
        request,
        "storage/reservation_table.html",
        {
            "units": units,
            "reservations": reservations,
            "bank_iban": config.ACCOUNT_IBAN,
            "bank_bic": config.ACCOUNT_BIC,
            "bank_name": config.ACCOUNT_NAME,
        },
    )
