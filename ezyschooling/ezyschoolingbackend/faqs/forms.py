from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import *


class CityDistrictFaqForm(forms.ModelForm):
    faq_answer  = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = CityDistrictFaq
        fields = "__all__"

class CityDistrictBoardFaqForm(forms.ModelForm):
    faq_answer  = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = CityDistrictBoardFaq
        fields = "__all__"

class CityDistrictSchoolTypeFaqForm(forms.ModelForm):
    faq_answer  = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = CityDistrictSchoolTypeFaq
        fields = "__all__"

class CityDistrictCoedFaqForm(forms.ModelForm):
    faq_answer  = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = CityDistrictCoedFaq
        fields = "__all__"

class CityDistrictGradeFaqForm(forms.ModelForm):
    faq_answer  = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = CityDistrictGradeFaq
        fields = "__all__"
