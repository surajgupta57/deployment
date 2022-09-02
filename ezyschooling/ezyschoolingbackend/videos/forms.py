from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import ExpertUserVideo


class ExpertUserVideoAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = ExpertUserVideo
        fields = "__all__"
