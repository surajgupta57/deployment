from django.apps import AppConfig


class NewslettersConfig(AppConfig):
    name = 'newsletters'

    def ready(self):
        import newsletters.signals
