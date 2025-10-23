from django.contrib.sites.models import Site
from drfx import config

def external_urls(request):
    site = Site.objects.get_current()
    return {
        "ASSOCIATION_RULES_URL": config.ASSOCIATION_RULES_URL,
        "MEMBERS_GUIDE_URL": config.MEMBERS_GUIDE_URL,
        "SITENAME": site.name,
        "SITE_URL": site.domain,
        "GITHUB_URL": config.GITHUB_URL,
        "PRIVACY_POLICY_URL": config.PRIVACY_POLICY_URL,
        "NFC_WIKI_URL": config.NFC_WIKI_URL,
    }
