from django.contrib.auth import get_user_model
from django.contrib import admin as django_admin
from django.test import TestCase
from django.utils import timezone

from users import models
from users.admin import CustomUserAdmin
from users.serializers import UserSerializer
from rest_framework.test import APIRequestFactory


class InstructorRoleModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="instructor_model@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="nick1",
            phone="+358111111",
        )

    def test_default_false(self):
        self.assertFalse(self.user.is_instructor, "Default is_instructor should be False")

    def test_can_set_true(self):
        self.user.is_instructor = True
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_instructor, "is_instructor persisted as True after save")


class InstructorRoleAdminTests(TestCase):
    def test_admin_fieldsets_include_is_instructor(self):
        admin_instance = CustomUserAdmin(models.CustomUser, django_admin.site)
        fieldset_fields = []
        for _title, opts in admin_instance.fieldsets:
            fieldset_fields.extend(list(opts.get("fields", ())))
        self.assertIn("is_instructor", fieldset_fields, "Edit form should include is_instructor")

        add_fieldset_fields = []
        for _title, opts in admin_instance.add_fieldsets:
            add_fieldset_fields.extend(list(opts.get("fields", ())))
        self.assertIn("is_instructor", add_fieldset_fields, "Add form should include is_instructor")

class InstructorRoleSerializerUnitTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="instructor_api@example.com",
            birthday=timezone.now().date(),
            municipality="City",
            nick="nick2",
            phone="+358222222",
        )

    def test_serializer_has_readonly_is_instructor(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        serializer = UserSerializer(instance=self.user, context={"request": request})
        self.assertIn("is_instructor", serializer.fields)
        self.assertTrue(
            serializer.fields["is_instructor"].read_only,
            "is_instructor should be read-only in UserSerializer",
        )

    def test_serializer_value_reflects_model(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        data = UserSerializer(instance=self.user, context={"request": request}).data
        self.assertIn("is_instructor", data)
        self.assertFalse(data["is_instructor"])

        self.user.is_instructor = True
        self.user.save()
        request2 = factory.get("/")
        data2 = UserSerializer(instance=self.user, context={"request": request2}).data
        self.assertTrue(data2["is_instructor"])
