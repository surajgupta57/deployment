from ckeditor.widgets import CKEditorWidget
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms

from .models import Personality, Quiz


class PersonalityAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Personality
        fields = "__all__"


class QuizEmailDashboardForm(forms.Form):
    subject = forms.CharField(max_length=100)
    preview = forms.CharField(widget=forms.Textarea,
                              label="Preview Text")
    quizzes = forms.ModelMultipleChoiceField(queryset=Quiz.objects.filter(roll_out=True),
                                             widget=FilteredSelectMultiple(
                                                 "Quizzes", is_stacked=False))
    recipient = forms.EmailField(
        required=False, help_text="For testing purposes only, leave send to all unchecked when using this.", label="Recipient Email")
    send_all = forms.BooleanField(required=False, initial=False, label="Send to all")

    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',),
        }
        js = ('/admin/jsi18n',)

    def clean(self):
        super().clean()
        recipient = self.cleaned_data.get('recipient')
        send_all = self.cleaned_data.get('send_all')
        if not recipient and not send_all:
            raise forms.ValidationError('You need to fill either recipient or send to all.')
        if recipient and send_all:
            raise forms.ValidationError('You can only enter either of the two among send to all and recipient.')
        return self.cleaned_data

    def clean_quizzes(self):
        quizzes = self.cleaned_data['quizzes']
        return quizzes