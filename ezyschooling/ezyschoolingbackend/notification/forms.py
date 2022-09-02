from django import forms
from schools.models import City
from .utils import get_city_list_tuple

class WebPushDashboardForm(forms.Form):
    title = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'cols': 40}),
        max_length=60,
        help_text="Max Length is 60 characters.")
    url = forms.URLField(
        help_text="Link that should be opened upon clicking the notification")
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'cols': 40}),
        max_length=130,
        help_text="Max Length is 130 characters.")
    image = forms.URLField(
        required=False,
        help_text="Article/News Thumbnail URL")
    icon = forms.URLField(
        required=False,
        help_text="Icon URL, you can put school logo or ezyschooling logo",
        initial="https://ezyschooling.com/favicon.png")

    def clean(self):
        super().clean()
        recipient = self.cleaned_data.get('image')
        send_all = self.cleaned_data.get('icon')
        if not recipient and not send_all:
            raise forms.ValidationError(
                'You need to fill either image or icon.')
        if recipient and send_all:
            raise forms.ValidationError(
                'You can only enter either of the two among icon and image')
        return self.cleaned_data

class NewWebPushDashboardForm(forms.Form):
    city_list = get_city_list_tuple()
    category_choices = [("all","All"),("boarding", "Boarding Schools"),("online", "Online Schools")]
    title = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'cols': 40}),
        max_length=200,
        help_text="Max Length is 200 characters.")
    click_action = forms.URLField(
        help_text="Link that should be opened upon clicking the notification")
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'cols': 40}),
        max_length=130,
        help_text="Max Length is 130 characters.")
    image_url = forms.URLField(
        required=False,
        help_text="Article/News Thumbnail URL")
    for_mobile_users = forms.BooleanField(required=False,help_text="Notification only for mobile user?")
    for_desktop_users = forms.BooleanField(required=False,help_text="Notification only for web user?")
    online_or_boarding = forms.ChoiceField(choices=category_choices)
    city = forms.ChoiceField(choices=city_list, help_text="Only select city if 'All' is selected in above Online/Boarding school category section")
    def clean(self):
        super().clean()
        # recipient = self.cleaned_data.get('image')
        # send_all = self.cleaned_data.get('icon')
        # if not recipient and not send_all:
        #     raise forms.ValidationError(
        #         'You need to fill either image or icon.')
        # if recipient and send_all:
        #     raise forms.ValidationError(
        #         'You can only enter either of the two among icon and image')
        return self.cleaned_data
