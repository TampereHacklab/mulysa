#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
from decimal import Decimal

from django.db.utils import IntegrityError

from users.models import BankTransaction, CustomUser, MemberService, ServiceSubscription

from utils.businesslogic import BusinessLogic
from utils.holvitoolbox import HolviToolbox

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Raised when the data has invalid value"""

    pass


"""
This class contains static members to import data to Mulysa. Data can be:

 - Member data. Current implementation imports CSV file used by old
   Tampere hacklab registry. It is only for reference - write your
   own importer!

 - Bank events. This is in form of bank transactions in and out of an
   account. Only one account is supported currently.
   Current implementation uses Nordea TITO format which seems to be
   some kind of standard.
   Use it if you can or write your own importer.

After data is imported, businesslogic to update all user data is
invoked. All functions return an object showing counts of imported,
already existing and failed items and array of failed rows. These
are displayed in the import UI.
"""


class DataImport:

    # Import cvs member list. Only for reference.
    @staticmethod
    def importmembers(f):
        csv = f.read().decode("utf8")
        lines = csv.split("\n")
        imported = exists = error = 0
        failedrows = []

        service_mo = MemberService.objects.get(name="Vuosimaksu")
        service_ar = MemberService.objects.get(name="Tilankäyttöoikeus")

        # Ignore header line
        for line in lines[1:]:
            try:
                line = line.replace('"', "")
                fields = line.split(",")
                if len(fields) < 13:
                    raise ParseError("Not enough fields on this row")
                name = fields[3].split(" ")
                first_name = ""
                last_name = ""

                if len(name) < 2:
                    raise ParseError("No proper name supplied: " + str(name))

                first_name = name[0]
                last_name = name[len(name) - 1]

                birthday = None
                try:
                    birthday = datetime.date.fromisoformat(fields[5])
                except ValueError as err:
                    print(
                        "Unable to parse ISO date: {}, error: {}", fields[5], str(err)
                    )
                try:
                    birthday = datetime.datetime.strptime(fields[5], "%Y/%m/%d")
                except ValueError as err:
                    print(
                        "Unable to parse / separated date: {}, error: {}",
                        fields[5],
                        str(err),
                    )
                try:
                    birthday = datetime.datetime.strptime(fields[5], "%Y-%m-%d")
                except ValueError as err:
                    print(
                        "Unable to parse - separated date: {}, error: {}",
                        fields[5],
                        str(err),
                    )

                if not birthday:
                    birthday = datetime.date(day=1, month=1, year=1970)

                # Todo: how to really interpret these
                membership_plan = "MO"
                if fields[2] == "1":
                    membership_plan = "AR"

                phone = fields[8]
                # Fix missing international prefix
                if len(phone) > 0 and phone[0] == "0":
                    phone = "+358" + phone[1:]

                newuser = CustomUser.objects.create_customuser(
                    first_name=first_name,
                    last_name=last_name,
                    email=fields[4],
                    birthday=birthday,
                    municipality=fields[6],
                    nick=fields[7],
                    phone=phone,
                )
                newuser.log("User imported")

                # Setup member service subscriptions

                ServiceSubscription.objects.create(
                    user=newuser, service=service_mo, state=ServiceSubscription.OVERDUE
                )
                if membership_plan == "AR":
                    ServiceSubscription.objects.create(
                        user=newuser,
                        service=service_ar,
                        state=ServiceSubscription.OVERDUE,
                    )

                imported = imported + 1
            except IntegrityError as err:
                print("Integrity error:", str(err))
                exists = exists + 1
                failedrows.append(line + " (" + str(err) + ")")
            except ParseError as err:
                print("Parse error: ", str(err))
                error = error + 1
                failedrows.append(line + " (" + str(err) + ")")
            except ValueError as err:
                print("Value error: ", str(err))
                error = error + 1
                failedrows.append(line + " (" + str(err) + ")")

        return {
            "imported": imported,
            "exists": exists,
            "error": error,
            "failedrows": failedrows,
        }

    # Nordea TITO import. TITO spec here: https://www.nordea.fi/Images/146-84478/xml_tiliote.pdf
    # Note: this is the text-based TITO, not XML.
    @staticmethod
    def import_tito(f):
        tito = f.read().decode("utf8")
        lines = tito.split("\n")
        imported = exists = error = 0
        failedrows = []
        for line in lines[1:]:
            logger.debug(f"import_tito - Processing line: {line}")
            try:
                if len(line) == 0 or line[0] != "T":
                    raise ParseError("Empty line or not starting with T")
                data_type = int(line[1:3])
                # Currently handle only type 10 (basic transaction data)
                if data_type == 10:
                    if int(line[3:6]) != 188 or len(line) != 188:
                        raise ParseError("Length should be 188")
                    transaction_id = line[6:12]
                    archival_reference = line[12:30].strip()
                    if len(archival_reference) < 18:
                        raise ParseError(
                            "Archival reference number invalid: " + archival_reference
                        )
                    transaction_date = datetime.datetime.strptime(line[30:36], "%y%m%d")
                    transaction_type = int(line[48])
                    if transaction_type < 1 or transaction_type > 4:
                        raise ParseError(
                            "Transaction type should be between 1 and 4, not "
                            + str(transaction_type)
                        )
                    code = line[49:52]
                    message = line[52:87].strip()
                    if message == "Viitemaksu":
                        message = None
                    amount = int(line[87:106]) / 100
                    peer = line[108:143]
                    peer = peer.replace("[", "Ä")
                    peer = peer.replace("]", "Å")
                    peer = peer.replace("\\", "Ö")
                    # tito format has leading zeroes in reference number, strip them
                    reference = line[159:179].strip().lstrip("0")

                    # Done parsing, add the transaction

                    try:
                        # Archival reference should be unique ID
                        BankTransaction.objects.get(
                            archival_reference=archival_reference
                        )
                        exists = exists + 1
                    except BankTransaction.DoesNotExist:
                        transaction = BankTransaction.objects.create(
                            date=transaction_date,
                            amount=amount,
                            reference_number=reference,
                            sender=peer,
                            archival_reference=archival_reference,
                            transaction_id=transaction_id,
                            code=code,
                        )
                        BusinessLogic.new_transaction(transaction)
                        imported = imported + 1
            except ParseError as err:
                logger.error(f"Error parsing data: {err}")
                error = error + 1
                failedrows.append(line + " (" + str(err) + ")")

        results = {
            "imported": imported,
            "exists": exists,
            "error": error,
            "failedrows": failedrows,
        }
        logger.info(f"Data imported: {results} - now updating all users..")

        BusinessLogic.update_all_users()

        return results

    # Holvi TITO import. TITO spec here: ???
    # Note: this is the XSL-based TITO.
    @staticmethod
    def import_holvi(f):
        holvi = HolviToolbox.parse_account_statement(f)
        imported = exists = error = 0
        failedrows = []
        for line in holvi:
            logger.debug(f"import_holvi - Processing line: {line}")
            try:
                if len(line) == 0:
                    raise ParseError("Empty line")
                archival_reference = line["Filing ID"].strip()
                if len(archival_reference) < 32:
                    raise ParseError(
                        "Archival reference number invalid: " + archival_reference
                    )
                transaction_date = line["Date_parsed"]
                message = line["Message"].strip()
                if message == "Viitemaksu":
                    message = None
                amount = Decimal(line["Amount"])
                peer = line["Counterparty"]
                # holvi reference has leading zeroes, clean them up here also
                reference = line["Reference"].strip().lstrip("0")

                # Done parsing, add the transaction

                try:
                    # Archival reference should be unique ID
                    BankTransaction.objects.get(archival_reference=archival_reference)
                    exists = exists + 1
                except BankTransaction.DoesNotExist:
                    transaction = BankTransaction.objects.create(
                        date=transaction_date,
                        amount=amount,
                        reference_number=reference,
                        sender=peer,
                        archival_reference=archival_reference,
                    )
                    BusinessLogic.new_transaction(transaction)
                    imported = imported + 1
            except ParseError as err:
                logger.error(f"Error parsing data: {err}")
                error = error + 1
                failedrows.append(line + " (" + str(err) + ")")

        results = {
            "imported": imported,
            "exists": exists,
            "error": error,
            "failedrows": failedrows,
        }
        logger.info(f"Data imported: {results} - now updating all users..")

        BusinessLogic.update_all_users()

        return results
