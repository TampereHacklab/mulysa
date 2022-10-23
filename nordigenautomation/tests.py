import json
from requests.models import Response

from django.test import TestCase

from .models import Config, Requisition
from unittest import mock


# mock requests
# data for these is taken from https://ob.nordigen.com/api/docs
def mocked_requests_get(*args, **kwargs):
    response_content = ""
    request_url = kwargs.get("url", None)
    # print(f"mocking get request to: {request_url}")
    # institutions, bit truncated
    if request_url == "https://ob.nordigen.com/api/v2/institutions/?country=FI":
        response_content = json.dumps(
            [
                {
                    "id": "STRIPE_STPUIE21",
                    "name": "Stripe",
                    "bic": "STPUIE21",
                    "transaction_total_days": "730",
                    "countries": [
                        "SE",
                        "FI",
                    ],
                    "logo": "https://cdn.nordigen.com/ais/STRIPE_STPUIE21.png",
                    "payments": False,
                },
                {
                    "id": "WISE_TRWIGB22",
                    "name": "Wise",
                    "bic": "TRWIGB22",
                    "transaction_total_days": "730",
                    "countries": [
                        "NO",
                        "SE",
                        "FI",
                    ],
                    "logo": "https://cdn.nordigen.com/ais/WISE_TRWIGB22.png",
                    "payments": False,
                },
            ]
        )
    elif (
        request_url
        == "https://ob.nordigen.com/api/v2/requisitions/3fa85f64-5717-4562-b3fc-2c963f66afa6/"
    ):
        response_content = json.dumps(
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "created": "2022-10-23T16:11:45.737Z",
                "redirect": "string",
                "status": {
                    "short": "CR",
                    "long": "CREATED",
                    "description": "Requisition has been successfully created",
                },
                "institution_id": "string",
                "agreement": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "reference": "string",
                "accounts": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
                "user_language": "string",
                "link": "https://ob.nordigen.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/{$INSTITUTION_ID}",
                "ssn": "string",
                "account_selection": False,
                "redirect_immediate": False,
            }
        )
    elif (
        request_url
        == "https://ob.nordigen.com/api/v2/accounts/3fa85f64-5717-4562-b3fc-2c963f66afa6/transactions/"
    ):
        response_content = json.dumps(
            {
                "transactions": {
                    "booked": [
                        {
                            "transactionId": "string",
                            "debtorName": "string",
                            "debtorAccount": {"iban": "string"},
                            "transactionAmount": {
                                "currency": "string",
                                "amount": "328.18",
                            },
                            "bankTransactionCode": "string",
                            "bookingDate": "date",
                            "valueDate": "date",
                            "remittanceInformationUnstructured": "string",
                        },
                        {
                            "transactionId": "string",
                            "transactionAmount": {
                                "currency": "string",
                                "amount": "947.26",
                            },
                            "bankTransactionCode": "string",
                            "bookingDate": "date",
                            "valueDate": "date",
                            "remittanceInformationUnstructured": "string",
                        },
                    ],
                    "pending": [
                        {
                            "transactionAmount": {
                                "currency": "string",
                                "amount": "float",
                            },
                            "valueDate": "date",
                            "remittanceInformationUnstructured": "string",
                        }
                    ],
                }
            }
        )
    elif request_url == "https://ob.nordigen.com/api/v2/institutions/?country=FI":
        response_content = json.dumps(
            [
                {
                    "id": "STRIPE_STPUIE21",
                    "name": "Stripe",
                    "bic": "STPUIE21",
                    "transaction_total_days": "730",
                    "countries": [
                        "SE",
                        "FI",
                    ],
                    "logo": "https://cdn.nordigen.com/ais/STRIPE_STPUIE21.png",
                    "payments": False,
                },
                {
                    "id": "WISE_TRWIGB22",
                    "name": "Wise",
                    "bic": "TRWIGB22",
                    "transaction_total_days": "730",
                    "countries": [
                        "NO",
                        "SE",
                        "FI",
                    ],
                    "logo": "https://cdn.nordigen.com/ais/WISE_TRWIGB22.png",
                    "payments": False,
                },
            ]
        )
    response = Response()
    response.status_code = 200
    response._content = str.encode(response_content)
    return response


def mocked_requests_post(*args, **kwargs):
    response_content = ""
    request_url = kwargs.get("url", None)
    # print(f"mocking post request to: {request_url}")
    # always return a valid token
    if request_url == "https://ob.nordigen.com/api/v2/token/new/":
        response_content = json.dumps(
            {
                "access": "string",
                "access_expires": 86400,
                "refresh": "string",
                "refresh_expires": 2592000,
            }
        )
    # and refreshtoken too
    elif request_url == "https://ob.nordigen.com/api/v2/token/refresh/":
        response_content = json.dumps({"access": "string", "access_expires": 86400})

    elif request_url == "https://ob.nordigen.com/api/v2/agreements/enduser/":
        response_content = json.dumps(
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "created": "2022-10-23T15:34:20.737Z",
                "max_historical_days": 90,
                "access_valid_for_days": 90,
                "access_scope": ["balances", "details", "transactions"],
                "accepted": "2022-10-23T15:34:20.737Z",
                "institution_id": "string",
            }
        )
    elif request_url == "https://ob.nordigen.com/api/v2/requisitions/":
        response_content = json.dumps(
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "created": "2022-10-23T15:35:36.938Z",
                "redirect": "string",
                "status": {
                    "short": "CR",
                    "long": "CREATED",
                    "description": "Requisition has been successfully created",
                },
                "institution_id": "string",
                "agreement": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "reference": "string",
                "accounts": [],
                "user_language": "string",
                "link": "https://ob.nordigen.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/TEST",
                "ssn": "string",
                "account_selection": False,
                "redirect_immediate": False,
            }
        )
    response = Response()
    response.status_code = 200
    response._content = str.encode(response_content)
    return response


class NordigenAutomationTests(TestCase):
    """
    Test nordigen. Mocks the whole Nordigen api
    """

    def setUp(self):
        # create config object to use
        self.config = Config()
        self.config.api_id = "testid"
        self.config.api_key = "testkey"
        self.config.country = "FI"
        self.config.institution = "Stripe"
        self.config.save()

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_requsition(self, mock_get, mock_post):
        """
        Test adding new requisition and deprecating old ones

        All real request to nordigen are mocked
        """
        # no active requsitions
        self.assertIsNone(self.config.get_active_requisition())

        # add new requisition
        req = self.config.create_new_requisition()
        # check that we have a link
        self.assertEqual(
            req.link,
            "https://ob.nordigen.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/TEST",
        )
        # and id
        self.assertEqual(req.requisition_id, "3fa85f64-5717-4562-b3fc-2c963f66afa6")

        # and we still don't have active requisition as it has not been finalized yet
        self.assertIsNone(self.config.get_active_requisition())

        # mark our new requisition as completed
        req.mark_completed()

        # and now we have active requisition for the config
        self.assertIsNotNone(self.config.get_active_requisition())

        # do another requisition, it should not become the active one
        req2 = self.config.create_new_requisition()
        self.assertNotEqual(self.config.get_active_requisition().id, req2.id)

        # activate the new one and becomes the active one and the old one gets deprecated
        req2.mark_completed()
        self.assertEqual(self.config.get_active_requisition().id, req2.id)

        req.refresh_from_db()
        self.assertTrue(req.deprecated)

        # test that we get transactions
        transactions = req2.get_transactions()
        self.assertEqual(len(transactions["transactions"]["booked"]), 2)

        # test that our active manager gets the req2
        self.assertIn(req2, Requisition.active.all())

        # and check that req is not in active manager
        self.assertNotIn(req, Requisition.active.all())

    def tearDown(self):
        self.config.delete()
