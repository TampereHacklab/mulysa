from constance import config
from django.conf import settings


# A class that accesses configuration variables from constance or settings
class ConfigAccessor(object):
    def __getattr__(self, key):
        try:
            value = getattr(config, key, None)
            return value if value is not None else getattr(settings, key)
        except AttributeError:
            raise AttributeError(
                f"Config variable {key} not found in constance configuration or local settings"
            )
