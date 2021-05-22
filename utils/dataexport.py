#!/usr/bin/env python
# -*- coding: utf-8 -*-

from users.models import CustomInvoice, CustomUser, MemberService, ServiceSubscription
import csv
import io


"""
This class contains static members to export data to Mulysa.
"""


class DataExport:
    # Export members as TSV. Probably can be removed quite soon. Contains hardcoded stuff!
    @staticmethod
    def exportmembers():
        tko = 2
        out = ""
        users = CustomUser.objects.all()
        for user in users:
            tko_ref = ""
            tko_service = MemberService.objects.get(id=tko)
            services = ServiceSubscription.objects.filter(
                user=user, service=tko_service
            )
            if len(services) == 1:
                tko_ref = services[0].reference_number
                if not tko_ref:
                    tko_ref = ""

            out += f"{user.first_name}\t{user.last_name}\t{user.phone}\t{tko_ref}\n"
        return out

    @staticmethod
    def exportaccounting():
        output = io.StringIO()

        fields = ["reference_number", "type", "accounting_id", "comment"]
        writer = csv.DictWriter(output, fieldnames=fields)

        writer.writeheader()

        subscriptions = ServiceSubscription.objects.all()
        for subscription in subscriptions:
            writer.writerow(
                {
                    "reference_number": subscription.reference_number,
                    "type": "service_subscription",
                    "accounting_id": subscription.service.accounting_id,
                    "comment": subscription.__str__(),
                },
            )

        custominvoices = CustomInvoice.objects.all()
        for custominvoice in custominvoices:
            writer.writerow(
                {
                    "reference_number": custominvoice.reference_number,
                    "type": "custominvoice",
                    "accounting_id": custominvoice.subscription.service.accounting_id,
                    "comment": custominvoice.subscription.__str__(),
                },
            )

        return output.getvalue()
