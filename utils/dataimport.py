#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from django.db.utils import IntegrityError

from users.models import BankTransaction, CustomUser


class ParseError(Exception):
    """Raised when the data has invalid value"""
    pass

class DataImport:

    @staticmethod
    def importmembers(f):
        csv = f.read().decode('utf8')
        lines = csv.split('\n')
        imported = exists = error = 0
        failedrows = []

        # Ignore header line
        for line in lines[1:]:
            try:
                line = line.replace('"', '')
                fields = line.split(',')
                print(fields)
                if len(fields) < 13:
                    raise ValueError('Not enough fields on this row')
                name = fields[3].split(' ')
                first_name = ''
                last_name = ''

                if len(name) < 2:
                    raise ValueError('No proper name supplied: ' + str(name))

                first_name = name[0]
                last_name = name[len(name)-1]

                birthday = None
                try:
                    birthday = datetime.date.fromisoformat(fields[5])
                except ValueError as err:
                    print('Unable to parse ISO date: {}, error: {}', fields[5], str(err))
                try:
                    birthday = datetime.datetime.strptime(fields[5], '%Y/%m/%d')
                except ValueError as err:
                    print('Unable to parse / separated date: {}, error: {}', fields[5], str(err))
                try:
                    birthday = datetime.datetime.strptime(fields[5], '%Y-%m-%d')
                except ValueError as err:
                    print('Unable to parse - separated date: {}, error: {}', fields[5], str(err))

                # Todo: how to really interpret these
                membership_plan = 'MO'
                if fields[2] == '1':
                    membership_plan = 'AR'

                newuser = CustomUser.objects.create_customuser(
                    reference_number=fields[1],
                    first_name=first_name,
                    last_name=last_name,
                    email=fields[4],
                    birthday=birthday,
                    municipality=fields[6],
                    nick=fields[7],
                    phone=fields[8],
                    membership_plan=membership_plan
                )
                newuser.log('User imported')
                imported = imported + 1
            except IntegrityError as err:
                print('Integrity error:', str(err))
                exists = exists + 1
                failedrows.append(line + ' (' + str(err) + ')')
            except ValueError as err:
                print('Value error: ', str(err))
                error = error + 1
                failedrows.append(line + ' (' + str(err) + ')')

        return {'imported': imported, 'exists': exists, 'error': error, 'failedrows': failedrows}

    @staticmethod
    def import_tito(f):
        tito = f.read().decode('utf8')
        lines = tito.split('\n')
        imported = exists = error = 0
        failedrows = []
        for line in lines[1:]:
            try:
                if len(line) == 0 or line[0] != 'T':
                    raise ParseError('Empty line or not stating with T')
                data_type = int(line[1:3])
                # Currently handle only type 10 (basic transaction data)
                if data_type == 10:
                    if int(line[3:6]) != 188:
                        raise ParseError('Length should be 188')
                    transaction_id = line[6:12]
                    print('tid', transaction_id)
                    archival_reference = line[12:30].strip()
                    if(len(archival_reference) < 18):
                        raise ParseError('Archival reference number invalid: ' + archival_reference)
                    print('an', archival_reference)
                    transaction_date = datetime.datetime.strptime(line[30:36], '%y%m%d')
                    print('date', transaction_date)
                    transaction_type = int(line[48])
                    if transaction_type < 1 or transaction_type > 4:
                        raise ParseError('Transaction type should be between 1 and 4, not ' + str(transaction_type))
                    print('type', transaction_type)
                    code = line[49:52]
                    print('code', code)
                    message = line[52:87].strip()
                    if message == 'Viitemaksu':
                        message = None
                    print('msg', message)
                    amount = int(line[87:106]) / 100
                    print('amount', amount)
                    peer = line[108:143]
                    peer = peer.replace('[', 'Ä')
                    peer = peer.replace(']', 'Å')
                    peer = peer.replace('\\\\', 'Ö')
                    print('peer', peer)
                    reference = line[159:179].strip()
                    if len(reference) > 0:
                        reference = int(reference)
                    else:
                        reference = None
                    print('ref', reference)

                    # Done parsing, add the transaction

                    try:
                        BankTransaction.objects.get(archival_reference=archival_reference)
                        exists = exists + 1
                        print('Transaction with archival ref ', archival_reference, ' already exists')
                    except BankTransaction.DoesNotExist:
                        transaction_user = None
                        if reference and reference > 0:
                            try:
                                transaction_user = CustomUser.objects.get(reference_number=reference)
                            except CustomUser.DoesNotExist:
                                pass

                        BankTransaction.objects.create(
                            user=transaction_user,
                            date=transaction_date,
                            amount=amount,
                            reference_number=reference,
                            sender=peer,
                            archival_reference=archival_reference
                        )
                        if transaction_user:
                            transaction_user.log('Bank transaction of ' +
                                str(amount) + '€ dated ' + str(transaction_date))

                        imported = imported + 1
            except ParseError as err:
                print('Error parsing data: ', str(err))
                error = error + 1
                failedrows.append(line + ' (' + str(err) + ')')
        return {'imported': imported, 'exists': exists, 'error': error, 'failedrows': failedrows}


# DataImport.import_tito(open('tito.nda', 'rb'))
