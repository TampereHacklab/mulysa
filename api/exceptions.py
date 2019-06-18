"""
Generic exception classes for everybody to use
"""

from rest_framework.exceptions import APIException


class NotImplementedYet(APIException):
    status_code = 501
    default_detail = 'This method has not been totally implemented yet'
    default_code = 'not_implemented'
