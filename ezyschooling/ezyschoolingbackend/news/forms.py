
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import News


class NewsAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = News
        fields = "__all__"


class NewsEmailDashboardForm(forms.Form):
    subject = forms.CharField(max_length=100)
    preview = forms.CharField(widget=forms.Textarea,
                              label="Preview Text")
    news = forms.ModelMultipleChoiceField(queryset=News.objects.filter(status=News.PUBLISHED).order_by("-timestamp"),
                                          help_text="This week's top 5 news items will be preselected by default, if you wish to change you're free to do so.",
                                          widget=FilteredSelectMultiple(
        "News Items", is_stacked=False))
    recipient = forms.EmailField(
        required=False, help_text="For testing purposes only, leave send to all unchecked when using this.", label="Recipient Email")
    send_all = forms.BooleanField(
        required=False, initial=False, label="Send to all")

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
            raise forms.ValidationError(
                'You need to fill either recipient or send to all.')
        if recipient and send_all:
            raise forms.ValidationError(
                'You can only enter either of the two among send to all and recipient.')
        return self.cleaned_data

    def clean_quizzes(self):
        news = self.cleaned_data['news']
        return news
