import datetime

from django.db.utils import IntegrityError

from users.models import CustomUser, BankTransaction


class DataImport:
    def importmembers(self, f):
        csv = f.read().decode('utf8')
        lines = csv.split('\n')
        imported = exists = error = 0
        failedrows = []

        # Ignore header line
        ln = 1
        for line in lines[1:]:
            print('importing line', line, ln, len(lines))
            ln = ln + 1
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
                    raise ValueError('No proper name supplied: ' + name)

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
                    print('Unable to parse other date: {}, error: {}', fields[5], str(err))

                # Todo: how to really interpret these
                membership_plan = 'MO'
                if fields[2] == '1':
                    membership_plan = 'AR'

                CustomUser.objects.create_customuser(
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

    def importnordea(self, f):
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
                if len(fields) < 4:
                    raise ValueError('Not enough fields on this row')
                transaction_date = None
                try:
                    transaction_date = datetime.datetime.fromisoformat(fields[0])
                except ValueError as err:
                    print('Unable to parse ISO date: {}, error: {}', fields[0], str(err))

                transaction_sender = fields[1]
                # Fix encoding
                transaction_sender = transaction_sender.replace('[', 'Ä')
                transaction_sender = transaction_sender.replace(']', 'Å')
                transaction_sender = transaction_sender.replace('\\\\', 'Ö')

                transaction_user = None
                reference = int(fields[4])
                if reference > 0:
                    try:
                        transaction_user = CustomUser.objects.get(reference_number=reference)
                    except CustomUser.DoesNotExist:
                        pass

                BankTransaction.objects.create(
                    user=transaction_user,
                    date=transaction_date,
                    amount=fields[3],
                    reference_number=reference,
                    sender=transaction_sender
                )
                imported = imported + 1
            except IntegrityError as err:
                print('Integrity error: ', str(err))
                exists = exists + 1
                failedrows.append(line + ' (' + str(err) + ')')
            except ValueError as err:
                print('Value error: ', str(err))
                error = error + 1
                failedrows.append(line + ' (' + str(err) + ')')

        return {'imported': imported, 'exists': exists, 'error': error, 'failedrows': failedrows}
