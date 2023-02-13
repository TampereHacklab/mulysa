from django.conf import settings
from constance import config
from django.contrib.sites.models import Site

def external_urls(request):
    site = Site.objects.get_current()
    return {
        "ASSOCIATION_RULES_URL": config.ASSOCIATION_RULES_URL,
        "MEMBERS_GUIDE_URL": config.MEMBERS_GUIDE_URL,
        "GITHUB_URL": settings.GITHUB_URL,
        "SITENAME": site.name,
        "SITE_URL": site.domain,
        "PRIVACY_POLICY_URL": config.PRIVACY_POLICY_URL,
    }
