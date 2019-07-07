import datetime

from users.models import CustomUser

class DataImport:
    def importmembers(self, f):
        csv = f.read().decode('utf8')
        lines = csv.split('\n')

        # Ignore header line
        for line in lines[1:]:
            line = line.replace('"', '')
            fields = line.split(',')
            print(fields)
            name = fields[3].split(' ')
            first_name = ''
            last_name = ''

            if len(name) == 2:
                first_name = name[0]
                last_name = name[1]

            birthday = datetime.date.fromisoformat(fields[5])

            # Todo: how to really interpret these
            membership_plan = 'MO'
            if fields[2] == '1':
                membership_plan = 'AR'

            CustomUser.objects.create_customuser(
                reference_number = fields[1],
                first_name = first_name,
                last_name = last_name,
                email = fields[4],
                birthday = birthday,
                municipality = fields[6],
                nick = fields[7],
                phone = fields[8],
                membership_plan = membership_plan
            )
