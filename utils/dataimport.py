import datetime

from django.db.utils import IntegrityError

from users.models import CustomUser


class DataImport:
    def importmembers(self, f):
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

                if len(name) == 2:
                    first_name = name[0]
                    last_name = name[1]
                birthday = None
                try:
                    birthday = datetime.date.fromisoformat(fields[5])
                except ValueError as err:
                    print('Unable to parse ISO date: {}, error: {}', fields[5], str(err))

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
                print('User already exists ', str(err))
                exists = exists + 1
            except ValueError as err:
                print('Value error importing user: ', str(err))
                error = error + 1
                failedrows.append(line)

        return {'imported': imported, 'exists': exists, 'error': error, 'failedrows': failedrows}
