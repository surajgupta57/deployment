from django.apps import AppConfig


class ChildsConfig(AppConfig):
    name = "childs"

    def ready(self):
        import childs.signals
