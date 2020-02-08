from django.conf import settings


def external_urls(request):
    return {
        "ASSOCIATION_RULES_URL": settings.ASSOCIATION_RULES_URL,
        "MEMBERS_GUIDE_URL": settings.MEMBERS_GUIDE_URL
    }

