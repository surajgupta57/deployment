from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import Discussion


class DiscussionAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Discussion
        fields = "__all__"
