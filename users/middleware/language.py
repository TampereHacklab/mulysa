from drfx import config
from django.utils import translation


class UserLanguageMiddleware(object):
    """
    Handle users language.

    Checks users "language" attribute and uses that to change
    the response language

    Replaces old django-user-language-middleware package

    https://pyquestions.com/how-to-explicitly-set-django-language-in-django-session
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_response(self, request, response):
        user = getattr(request, "user", None)
        if not user:
            return response

        if not user.is_authenticated:
            return response

        user_language = getattr(user, "language", None)
        if not user_language:
            return response

        current_language = translation.get_language()
        if user_language == current_language:
            return response

        translation.activate(user_language)
        response.set_cookie(config.LANGUAGE_COOKIE_NAME, user_language)

        return response
