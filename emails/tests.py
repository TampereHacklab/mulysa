from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import html, timezone

from mailer.models import Message

from .models import Email


class EmailAdminTestCase(TestCase):
    """
    Test custom admin actions
    """

    def setUp(self):
        self.client = Client()
        self.email = Email.objects.create(
            subject="Test email 1",
            content="Test message 1\nWith\nNewlines\n and special characters öä'\"&<>\n\nand utf-8 test string ᚻᛖ ᚳᚹᚫᚦ ᚦᚫᛏ ᚻᛖ ᛒᚢᛞᛖ ᚩᚾ ᚦᚫᛗ ᛚᚪᚾᛞᛖ ᚾᚩᚱᚦᚹᛖᚪᚱᛞᚢᛗ ᚹᛁᚦ ᚦᚪ ᚹᛖᛥᚫ",
        )
        self.email_sent = Email.objects.create(
            subject="Test email 1",
            content="Test message 1\nWith\nNewlines",
            sent=timezone.now(),
        )
        self.user = get_user_model().objects.create_superuser(
            email="testsuper@example.com",
            first_name="test",
            last_name="super",
            phone="123123",
            password="abc123",
        )
        self.client.force_login(self.user)

    def test_listing_actions(self):
        url = reverse("admin:emails_email_changelist")
        response = self.client.get(url)
        self.assertContains(response, reverse("admin:email-send", args=[self.email.pk]))
        self.assertContains(response, "/email/" + self.email_sent.get_url())

    def test_send_preview(self):
        url = reverse("admin:email-send", args=[self.email.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, html.escape(self.email.content))

    def test_sending(self):
        self.assertIsNone(self.email.sent)
        url = reverse("admin:email-send", args=[self.email.pk])
        data = {"action": "email-send"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()

        # check that it was marked as sent
        self.assertIsNotNone(self.email.sent)

        # check that the view in browser is accessible
        url = "/email/" + self.email.get_url()
        preview = self.client.get(url)
        self.assertContains(preview, html.escape(self.email.content))

        # and check that non auth users cannot view it
        self.client.logout()
        not_authenticated_preview = self.client.get(url)
        self.assertEqual(not_authenticated_preview.status_code, 302)


class EmailTestCase(TestCase):
    def setUp(self):
        # few test emails
        self.email1 = Email.objects.create(
            subject="Test email 1",
            content="Test message 1\nWith\nNewlines\n and special characters öä'\"&<>\n\nand utf-8 test string ᚻᛖ ᚳᚹᚫᚦ ᚦᚫᛏ ᚻᛖ ᛒᚢᛞᛖ ᚩᚾ ᚦᚫᛗ ᛚᚪᚾᛞᛖ ᚾᚩᚱᚦᚹᛖᚪᚱᛞᚢᛗ ᚹᛁᚦ ᚦᚪ ᚹᛖᛥᚫ",
        )

        # one active user, one inactive user
        self.user1 = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.user1.is_active = True
        self.user1.save()
        self.user2 = get_user_model().objects.create_customuser(
            first_name="Another",
            last_name="User",
            email="user2@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user2",
            phone="+358321321",
        )
        self.user2.is_active = False
        self.user2.save()

    def test_email_object(self):
        email = Email.objects.get(subject="Test email 1")
        self.assertEqual(email.slug, "test-email-1")
        self.assertIsNone(email.sent)
        self.assertEqual(email.get_epoch(), "000")

    def test_queue_and_send(self):
        # queue our test message to queryset of recipients
        self.email1.queue_to_recipients(get_user_model().objects.filter(is_active=True))

        # now we should have one email in queue (the other user is not active)
        self.assertEqual(Message.objects.count(), 1)

        # check that the contents matches (newlines!)
        self.assertIn(self.email1.content, Message.objects.first().email.body)

        # check the epoch method now that sent is on
        self.email1.refresh_from_db()
        self.assertEqual(self.email1.get_epoch(), self.email1.sent.strftime("%s"))

    def tearDown(self):
        Email.objects.all().delete()
        get_user_model().objects.all().delete()
