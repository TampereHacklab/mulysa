#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
from decimal import Decimal

from users.models import BankTransaction

from utils.businesslogic import BusinessLogic
from utils.holvitoolbox import HolviToolbox

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Raised when the data has invalid value"""

    pass


"""
This class contains data importers

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
    # Nordea TITO import. TITO spec here: https://www.nordea.fi/Images/146-84478/xml_tiliote.pdf
    # Note: this is the text-based TITO, not XML.
    # DEPRECATED: but the decorator is only available after python 3.13
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
                    # normalize the line ending before checking the length
                    if int(line[3:6]) != 188 or len(line.rstrip("\r\n")) != 188:
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
                        # Archival reference with date is unique
                        BankTransaction.objects.get(
                            archival_reference=archival_reference, date=transaction_date
                        )
                        exists = exists + 1
                    except BankTransaction.DoesNotExist:
                        transaction = BankTransaction.objects.create(
                            archival_reference=archival_reference,
                            date=transaction_date,
                            amount=amount,
                            reference_number=reference,
                            sender=peer,
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
    # Note: this is the XLSX-based TITO.
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
                if message in ["Viitemaksu", "None"]:
                    message = None
                amount = Decimal(line["Amount"])
                peer = line["Counterparty"]
                # holvi reference has leading zeroes, clean them up here also
                reference = line["Reference"].strip().lstrip("0")

                # Done parsing, add the transaction

                try:
                    # Archival reference with date is unique
                    BankTransaction.objects.get(
                        archival_reference=archival_reference, date=transaction_date
                    )
                    exists = exists + 1
                except BankTransaction.DoesNotExist:
                    transaction = BankTransaction.objects.create(
                        archival_reference=archival_reference,
                        date=transaction_date,
                        amount=amount,
                        reference_number=reference,
                        sender=peer,
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

    @staticmethod
    def import_nordigen(data):
        """
        Importer for nordigen api response https://ob.nordigen.com/api/docs#/accounts/accounts_transactions_retrieve

        Takes the whole nordigen response but parses only the "booked" section from it (pending transactions do not count)
        """
        booked = data["transactions"]["booked"]
        imported = exists = error = 0

        failedrows = []
        for one in booked:
            logger.debug(f"import_nordigen - Processing entry: {one}")

            try:
                # map nordigen fields to our fields
                # NOTE: it seems that some banks give different fields
                # see: https://nordigen.com/en/docs/account-information/output/transactions/
                archival_reference = one["transactionId"]
                transaction_date = datetime.datetime.strptime(
                    one["bookingDate"], "%Y-%m-%d"
                ).date()
                if one["transactionAmount"]["currency"] != "EUR":
                    raise Exception("Cannot handle different currencies")
                amount = one["transactionAmount"]["amount"]
                reference = one.get("entryReference") or ""
                reference = reference.lstrip("0")
                sender = one.get("debtorName", "")
                message = one.get("additionalInformation", "")

                try:
                    # Archival reference with date is unique
                    BankTransaction.objects.get(
                        archival_reference=archival_reference, date=transaction_date
                    )
                    exists = exists + 1
                except BankTransaction.DoesNotExist:
                    transaction = BankTransaction.objects.create(
                        archival_reference=archival_reference,
                        date=transaction_date,
                        transaction_id=archival_reference,
                        amount=amount,
                        reference_number=reference,
                        sender=sender,
                        message=message,
                    )
                    BusinessLogic.new_transaction(transaction)
                    imported = imported + 1

            except Exception as e:
                logger.error(f"Error: {e}")
                error = error + 1
                failedrows.append(str(one) + " (" + str(e) + ")")

        results = {
            "imported": imported,
            "exists": exists,
            "error": error,
            "failedrows": failedrows,
        }

        logger.info(f"Data imported: {results} - now updating all users..")
        BusinessLogic.update_all_users()

        return results
