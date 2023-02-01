from django.contrib.auth.models import BaseUserManager
import datetime
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, first_name, last_name, phone, password):
        user = self.model(
            email=email, first_name=first_name, last_name=last_name, phone=phone
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True

        # fill in some dummy data as they are required.
        # when registration works this wont be needed (we just need a way
        # of elevating a user to staff status)
        user.birthday = datetime.datetime.now()

        user.save(using=self.db)
        return user

    def create_customuser(
        self,
        email,
        first_name,
        last_name,
        phone,
        birthday,
        municipality,
        nick,
    ):
        if not email:
            raise ValueError(_("User must have an email address"))

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            birthday=birthday,
            municipality=municipality,
            nick=nick,
        )

        user.save(using=self.db)
        return user
