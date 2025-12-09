from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import json

from api.models import AccessDevice, DeviceAccessLogEntry, AccessPermission
from users.models import BankTransaction, CustomUser, MemberService, ServiceSubscription


class TestBasicSmoke(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.banktransaction = BankTransaction.objects.create(
            date=timezone.now(),
            amount=10
        )

    def test_index_anon(self):
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(response, "Wanna join us")
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="fi")
        self.assertContains(response, "Haluatko liittyä")

    def test_changelog(self):
        self.client.logout()
        response = self.client.get(reverse("changelog-view"))
        self.assertNotEqual(response.status_code, 200)

        self.client.force_login(self.user)
        response = self.client.get(reverse("changelog-view"))
        self.assertContains(response, "Changelog")

    def test_secured_urls(self):
        """
        Just very crude test that the urls don't give 200 ok when not logged in
        """
        urls = [
            reverse("dataimport"),
            reverse("dataexport"),
            reverse("users"),
            reverse("users/create"),
            reverse("ledger"),
            reverse("custominvoices"),
            reverse("machine-access-control"),
            reverse("userdetails", args=(self.user.id,)),
            reverse("usersettings", args=(self.user.id,)),
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            reverse("usersettings_claim_nfc", args=(self.user.id,)),
            reverse("usersettings_delete_nfc", args=(self.user.id,)),
            reverse("custominvoice"),
            reverse("custominvoice_action", args=("test", 1)),
            reverse("application_operation", args=(1, "test")),
            reverse("banktransaction-view", args=(self.banktransaction.pk,)),
            reverse("graphs"),
        ]
        self.client.logout()
        for url in urls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertRedirects(response, f"/www/login/?next={url}", msg_prefix=f"{url}")

        api_urls = [
            reverse("banktransactionaggregate-list", args=()),
            reverse("banktransactionaggregate-detail", args=(1,)),
        ]
        for url in api_urls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertEqual(response.status_code, 401, f"{url}")

        # and some urls we should not see as basic logged in user
        self.client.force_login(self.user)
        ownurls = [
            reverse("dataimport"),
            reverse("dataexport"),
            reverse("users"),
            reverse("users/create"),
            reverse("ledger"),
            reverse("custominvoices"),
            reverse("machine-access-control"),
            reverse("application_operation", args=(1, "test")),
            reverse("banktransaction-view", args=(self.banktransaction.pk,)),
        ]
        for url in ownurls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertRedirects(response, f"/www/login/?next={url}", msg_prefix=f"{url}")

    def test_index_logged(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(response, "Welcome back")
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="fi")
        self.assertContains(response, "Tervetuloa takaisin")

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestUserViews(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)
        # test service
        self.memberservice = MemberService.objects.create(
            name="TestService", cost=10, days_per_payment=30, days_before_warning=2
        )

    def test_my_info(self):
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

        userdetails = response.context["userdetails"]
        self.assertEqual(len(userdetails.servicesubscriptions), 0)
        self.assertEqual(len(userdetails.transactions), 0)
        self.assertEqual(len(userdetails.custominvoices), 0)

    def test_instructor_badge_visibility(self):
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertNotContains(response, "Instructor")

        self.user.is_instructor = True
        self.user.save()
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, "Instructor")

    def test_update_data(self):
        # get data
        response = self.client.get(
            reverse("usersettings", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

        # post new data and check
        response = self.client.post(
            reverse("usersettings", args=(self.user.id,)),
            {"first_name": "New", "last_name": "Test"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New")
        self.assertContains(response, "Test")

    def test_subscribe_unsubscribe_invalid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # redirect to login as id does not match
        self.assertRedirects(
            response,
            reverse("login")
            + "?next="
            + reverse("usersettings_subscribe_service", args=(9999,)),
        )

        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # redirect to login as id does not match
        self.assertRedirects(
            response,
            reverse("login")
            + "?next="
            + reverse("usersettings_unsubscribe_service", args=(9999,)),
        )

        # become staff
        self.user.is_staff = True
        self.user.save()

        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # user not found
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # user not found
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            {"serviceid": 9999},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # service not found
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": 9999},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # service not found
        self.assertEqual(response.status_code, 404)

        self.client.logout()

    def test_subscribe_unsubscribe(self):
        # service not self subscribe
        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "This service cannot be self subscribed to")

        # change the service
        self.memberservice.self_subscribe = True
        self.memberservice.save()

        # subscibe again
        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Service subscribed. You may now pay for it."
        )

        # and check that we see it
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(len(response.context["userdetails"].servicesubscriptions), 1)

        # unsubscribe when not paid
        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": self.user.servicesubscription_set.first().id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Service is not active. You must pay for the service first. Contact staff if needed.",
        )

        # change the service to active
        ss = self.user.servicesubscription_set.first()
        ss.state = ServiceSubscription.ACTIVE
        ss.save()

        # unsubscribe again
        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": ss.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Service unsubscribed")

        # check that our log has the entries
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(
            response,
            f"Self subscribed to {self.memberservice.name}",
        )
        self.assertContains(
            response,
            f"Self unsubscribing from {self.memberservice.name}",
        )

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestStaffViews(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="Test",
            last_name="Admin",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

    def test_smoke_views(self):
        urls = [
            reverse("dataimport"),
            reverse("dataexport"),
            reverse("users"),
            reverse("users/create"),
            reverse("ledger"),
            reverse("custominvoices"),
            reverse("custominvoice"),
        ]
        for url in urls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        # with invalid data
        response = self.client.post(
            reverse("users/create"),
            {
                "first_name": "test_firstname",
                "last_name": "test_lastname",
                "email": "",
                "language": "fi",
                "municipality": "TestPlace",
                "nick": "testuser",
                "mxid": "",
                "birthday_year": "2000",
                "birthday_month": "1",
                "birthday_day": "1",
                "phone": "+358123123321",
            },
        )
        self.assertEqual(response.status_code, 200)

        # with valid data
        response = self.client.post(
            reverse("users/create"),
            {
                "first_name": "test_firstname",
                "last_name": "test_lastname",
                "email": "testuser@example.com",
                "language": "fi",
                "municipality": "TestPlace",
                "nick": "testuser",
                "mxid": "",
                "birthday_year": "2000",
                "birthday_month": "1",
                "birthday_day": "1",
                "phone": "+358123123321",
            },
        )
        u = CustomUser.objects.get(email="testuser@example.com")
        self.assertRedirects(response, reverse("userdetails", args=(u.id,)))

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestNFC(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="Test",
            last_name="Admin",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)

    def test_nfc(self):
        # no cards have been seen
        response = self.client.get(
            reverse("usersettings", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(
            response,
            "No recent unclaimed NFC cards. Go to door, use a card and claim it here in 5 minutes",
        )

        # simulate door access, by creating a new entry
        device = AccessDevice()
        device.save()
        logentry = DeviceAccessLogEntry()
        logentry.payload = "1234567"
        logentry.device = device
        logentry.method = "nfc"
        logentry.granted = False
        logentry.save()

        response = self.client.get(
            reverse("usersettings", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(len(response.context["unclaimed_nfccards"]), 1)

        # claim it
        response = self.client.post(
            reverse("usersettings_claim_nfc", args=(self.user.id,)),
            {"logentryid": logentry.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # the code is not found from the page anymore
        self.assertNotContains(response, logentry.payload)
        # got success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "NFC Card successfully claimed")
        # and the card censored id can be found
        self.user.refresh_from_db()
        cardcensoredid = self.user.nfccard_set.first().censored_id()
        self.assertContains(response, cardcensoredid)
        # and nothing in claims anymore
        self.assertNotContains(
            response,
            "No recent unclaimed NFC cards. Go to door, use a card and claim it here in 5 minutes",
        )

        # delete it
        response = self.client.post(
            reverse("usersettings_delete_nfc", args=(self.user.id,)),
            {"nfccardid": self.user.nfccard_set.first().id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # got success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "NFC Card successfully deleted")
        # and the card censored id can be found
        self.assertNotContains(response, cardcensoredid)
        # and nothing to claim
        self.assertContains(
            response,
            "No recent unclaimed NFC cards. Go to door, use a card and claim it here in 5 minutes",
        )

        # check that our log has the entries
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(
            response,
            f"Registered new NFC card {cardcensoredid}",
        )
        self.assertContains(
            response,
            f"Deleted NFC card {cardcensoredid}",
        )

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestAccessLogs(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)
        # create a device
        self.device = AccessDevice.objects.create(name="Main Door")

    def test_access_logs_requires_login(self):
        self.client.logout()
        url = reverse("useraccesslogs", args=(self.user.id,))
        response = self.client.get(url)
        self.assertRedirects(response, f"/www/login/?next={url}")

    def test_access_logs_visible_to_self_with_pagination(self):
        # create 25 log entries associated with user's phone
        for i in range(25):
            DeviceAccessLogEntry.objects.create(
                device=self.device,
                method="phone",
                payload=self.user.phone,
                granted=(i % 2 == 0),
            )

        url = reverse("useraccesslogs", args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # page 1 should have pagination and show Next
        self.assertContains(response, "Next")
        # go to page 2
        response = self.client.get(url + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Previous")

    def test_access_logs_visible_to_staff_for_other_user(self):
        other = get_user_model().objects.create_customuser(
            first_name="Other",
            last_name="User",
            email="other@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="otheruser",
            phone="+358999999",
        )
        # create a log entry for other user
        DeviceAccessLogEntry.objects.create(
            device=self.device,
            method="phone",
            payload=other.phone,
            granted=True,
        )
        # make current user staff
        self.user.is_staff = True
        self.user.save()
        url = reverse("useraccesslogs", args=(other.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_access_logs_not_visible_to_instructor_for_others(self):
        instructor = get_user_model().objects.create_customuser(
            first_name="Inst",
            last_name="Ructor",
            email="inst@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="instructor",
            phone="+358555555",
        )
        instructor.is_instructor = True
        instructor.save()
        # create a log entry for self to ensure page renders for own logs
        DeviceAccessLogEntry.objects.create(
            device=self.device,
            method="phone",
            payload=instructor.phone,
            granted=True,
        )

        self.client.force_login(instructor)
        # instructor can see own logs
        own_url = reverse("useraccesslogs", args=(instructor.id,))
        response = self.client.get(own_url)
        self.assertEqual(response.status_code, 200)

        # instructor cannot see other user's logs
        other_url = reverse("useraccesslogs", args=(self.user.id,))
        response = self.client.get(other_url)
        self.assertRedirects(response, f"/www/login/?next={other_url}")


class TestMachineAccessList(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)

    def test_machine_access_via_permission(self):
        perm = AccessPermission.objects.create(name="Cutter", code="cutter")
        machine = AccessDevice.objects.create(
            name="Laser Cutter",
            deviceid="laser-1",
            device_type=AccessDevice.DEVICE_TYPE_MACHINE,
        )
        machine.allowed_permissions.add(perm)
        # grant user the permission
        self.user.access_permissions.add(perm)

        response = self.client.get(reverse("userdetails", args=(self.user.id,)))
        self.assertContains(response, "Machine Access")
        self.assertContains(response, "Laser Cutter")

    def test_machine_access_via_service(self):
        # create a machine that requires a specific service
        service = MemberService.objects.create(name="Woodshop", cost=10, days_per_payment=30, days_before_warning=2)
        machine = AccessDevice.objects.create(
            name="Table Saw",
            deviceid="saw-1",
            device_type=AccessDevice.DEVICE_TYPE_MACHINE,
        )
        machine.allowed_services.add(service)
        # subscribe user to the service and mark active
        ServiceSubscription.objects.create(user=self.user, service=service, state=ServiceSubscription.ACTIVE)

        response = self.client.get(reverse("userdetails", args=(self.user.id,)))
        self.assertContains(response, "Table Saw")

    def test_no_machine_access_message(self):
        response = self.client.get(reverse("userdetails", args=(self.user.id,)))
        self.assertContains(response, "You currently do not have access to any machines.")


class TestMachineAccessControlView(TestCase):
    def setUp(self):
        self.member = get_user_model().objects.create_customuser(
            first_name="Bob",
            last_name="Member",
            email="bob@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="bob",
            phone="+358777777",
        )

        self.instructor = get_user_model().objects.create_customuser(
            first_name="Ina",
            last_name="Structor",
            email="ina@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="ina",
            phone="+358222222",
        )
        self.instructor.is_instructor = True
        self.instructor.save()

        self.admin = get_user_model().objects.create_customuser(
            first_name="Adam",
            last_name="Admin",
            email="adam@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="adam",
            phone="+358333333",
        )
        self.admin.is_staff = True
        self.admin.save()

        self.perm1 = AccessPermission.objects.create(name="Training A", code="train-a", education_required=True)
        self.perm2 = AccessPermission.objects.create(name="Training B", code="train-b", education_required=True)
        self.member.access_permissions.add(self.perm1)

        self.machine = AccessDevice.objects.create(
            name="CNC Router",
            deviceid="cnc-1",
            device_type=AccessDevice.DEVICE_TYPE_MACHINE,
        )
        self.machine.allowed_permissions.add(self.perm1, self.perm2)

    def test_search_member_for_instructor(self):
        self.instructor.access_permissions.add(self.perm1)
        self.client.force_login(self.instructor)
        url = reverse("search_member")
        response = self.client.get(url, {"member_number": str(self.member.id), "last_name": self.member.last_name})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["found"])
        self.assertEqual(data["user_id"], self.member.id)
        self.assertEqual(sorted(data["allowed_permissions"]), sorted(list(self.member.access_permissions.values_list("id", flat=True))))
        self.assertEqual(sorted(data["instructor_permissions"]), sorted(list(self.instructor.access_permissions.values_list("id", flat=True))))
        self.assertFalse(data["is_admin"])

    def test_search_member_for_admin(self):
        self.client.force_login(self.admin)
        url = reverse("search_member")
        response = self.client.get(url, {"member_number": str(self.member.id), "last_name": self.member.last_name})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_admin"])
        all_perm_ids = list(AccessPermission.objects.values_list("id", flat=True))
        self.assertEqual(sorted(data["instructor_permissions"]), sorted(all_perm_ids))

    def test_update_permission_instructor_without_required_perms(self):
        self.instructor.access_permissions.add(self.perm1)
        self.client.force_login(self.instructor)
        url = reverse("update_permission")
        response = self.client.post(url, {"user_id": self.member.id, "machine_id": self.machine.id, "checked": "true"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(sorted(list(self.member.access_permissions.values_list("id", flat=True))), sorted([self.perm1.id]))

    def test_update_permission_instructor_with_required_perms(self):
        self.instructor.access_permissions.add(self.perm1, self.perm2)
        self.client.force_login(self.instructor)
        url = reverse("update_permission")
        response = self.client.post(url, {"user_id": self.member.id, "machine_id": self.machine.id, "checked": "true"})
        self.assertEqual(response.status_code, 200)
        member_perm_ids = set(self.member.access_permissions.values_list("id", flat=True))
        self.assertTrue({self.perm1.id, self.perm2.id}.issubset(member_perm_ids))
        response = self.client.post(url, {"user_id": self.member.id, "machine_id": self.machine.id, "checked": "false"})
        self.assertEqual(response.status_code, 200)
        member_perm_ids = set(self.member.access_permissions.values_list("id", flat=True))
        self.assertFalse({self.perm1.id, self.perm2.id}.issubset(member_perm_ids))

    def test_update_permission_admin(self):
        self.client.force_login(self.admin)
        url = reverse("update_permission")
        response = self.client.post(url, {"user_id": self.member.id, "machine_id": self.machine.id, "checked": "true"})
        self.assertEqual(response.status_code, 200)
        member_perm_ids = set(self.member.access_permissions.values_list("id", flat=True))
        self.assertTrue({self.perm1.id, self.perm2.id}.issubset(member_perm_ids))
        response = self.client.post(url, {"user_id": self.member.id, "machine_id": self.machine.id, "checked": "false"})
        self.assertEqual(response.status_code, 200)
        member_perm_ids = set(self.member.access_permissions.values_list("id", flat=True))
        self.assertFalse({self.perm1.id, self.perm2.id}.issubset(member_perm_ids))


class TestInstructorAccessControl(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="Alice",
            last_name="Member",
            email="alice@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="alice",
            phone="+358111111",
        )

    def test_machine_access_control_requires_login(self):
        url = reverse("machine-access-control")
        response = self.client.get(url)
        self.assertRedirects(response, f"/www/login/?next={url}")

    def test_machine_access_control_denied_for_basic_user(self):
        self.client.force_login(self.user)
        url = reverse("machine-access-control")
        response = self.client.get(url)
        self.assertRedirects(response, f"/www/login/?next={url}")

    def test_machine_access_control_allowed_for_instructor(self):
        self.user.is_instructor = True
        self.user.save()
        self.client.force_login(self.user)
        url = reverse("machine-access-control")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Machine Access Control")

    def test_machine_access_control_allowed_for_staff(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        url = reverse("machine-access-control")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Machine Access Control")
