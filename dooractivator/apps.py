from django.apps import AppConfig


class DooractivatorConfig(AppConfig):
    name = "dooractivator"

    def ready(self):
        import dooractivator.signals  # noqa
