from django.apps import AppConfig


class AdmissionFormsConfig(AppConfig):
    name = "admission_forms"

    def ready(self):
        import admission_forms.signals
