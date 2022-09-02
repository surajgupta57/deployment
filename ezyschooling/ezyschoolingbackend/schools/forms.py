from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import AdmissionPageContent,SchoolProfile,BoardingSchoolExtend


class AdmissionPageContentAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = AdmissionPageContent
        fields = "__all__"

class SchoolProfileAdminForm(forms.ModelForm):
   description = forms.CharField(widget=CKEditorUploadingWidget())

   class Meta:
       model = SchoolProfile
       fields = "__all__"

class BoardingSchoolExtendFrom(forms.ModelForm):
   pre_post_admission_process = forms.CharField(widget=CKEditorUploadingWidget(),required=False)
   withdrawl_policy = forms.CharField(widget=CKEditorUploadingWidget(),required=False)
   food_details = forms.CharField(widget=CKEditorUploadingWidget(),required=False)

   class Meta:
       model = BoardingSchoolExtend
       fields = "__all__"

class AddNewIDForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        help_text="Max Length is 200 characters.")
    def clean(self):
        super().clean()
        return self.cleaned_data
