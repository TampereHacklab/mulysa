#!/usr/bin/env python
# -*- coding: utf-8 -*-

from users.models import CustomUser, MemberService, ServiceSubscription

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
            print("TKO Service", tko_service)
            services = ServiceSubscription.objects.filter(
                user=user, service=tko_service
            )
            print("Services", services)
            if len(services) == 1:
                tko_ref = services[0].reference_number
                if not tko_ref:
                    tko_ref = ""

            out += f"{user.first_name}\t{user.last_name}\t{user.phone}\t{tko_ref}\n"
        return out
