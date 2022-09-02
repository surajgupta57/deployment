from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import AdmissionInformationArticle, AdmissionInformationUserVideo, AdmissionInformationNews


class AdmissionInformationArticleAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = AdmissionInformationArticle
        fields = "__all__"


class AdmissionInformationNewsAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = AdmissionInformationNews
        fields = "__all__"


class AdmissionInformationUserVideoAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = AdmissionInformationUserVideo
        fields = "__all__"
