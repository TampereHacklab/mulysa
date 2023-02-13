from django.conf import settings
from constance import config

def external_urls(request):
    return {
        "ASSOCIATION_RULES_URL": config.ASSOCIATION_RULES_URL,
        "MEMBERS_GUIDE_URL": config.MEMBERS_GUIDE_URL,
        "GITHUB_URL": settings.GITHUB_URL,
        "SITENAME": config.SITENAME,
        "SITE_URL": config.SITE_URL,
        "PRIVACY_POLICY_URL": config.PRIVACY_POLICY_URL,
    }
