from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import ExpertArticle


class ExpertArticleAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = ExpertArticle
        fields = "__all__"
