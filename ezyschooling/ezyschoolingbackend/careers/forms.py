from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import JobProfile


class JobProfileAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = JobProfile
        fields = "__all__"
