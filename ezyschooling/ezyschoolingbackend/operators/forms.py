from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from admission_forms.models import SchoolApplication, ApplicationStatusLog, ApplicationStatus
from schools.models import SchoolProfile, DistancePoint, AgeCriteria, SchoolPoint
from django.contrib.admin.widgets import FilteredSelectMultiple
from admission_forms.models import CommonRegistrationForm
from parents.models import ParentProfile
from childs.models import Child
from dal import autocomplete
from bootstrap_datepicker_plus import DatePickerInput

class UserForm(UserCreationForm):
    name = forms.CharField()
    school = forms.ModelMultipleChoiceField(queryset=SchoolProfile.objects.filter(collab=False),
                                            widget=FilteredSelectMultiple(
        "Schools", is_stacked=False, attrs={}), required=False)

    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',),
        }
        js = ('/admin/jsi18n',)

    class Meta:
        model = User
        fields = ['name', 'username', 'password1', 'password2', 'school']


class OperatorEditForm(forms.ModelForm):
    school = forms.ModelMultipleChoiceField(queryset=SchoolProfile.objects.filter(collab=False),
                                            widget=FilteredSelectMultiple(
        "Schools", is_stacked=False, attrs={}), required=False)

    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',),
        }
        js = ('/admin/jsi18n',)

    class Meta:
        model = Operator
        fields = ("id", "name", "credit", "school",)


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(
        attrs={
            "class": "form-control"
        }))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "id": "user-password"
            }
        )
    )


class CommonForm(forms.ModelForm):
    sibling1_alumni_school_name = forms.ModelChoiceField(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
            required=False,
            queryset=SchoolProfile.objects.filter(is_verified=True, is_active=True))
    sibling2_alumni_school_name = forms.ModelChoiceField(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
            required=False,
            queryset=SchoolProfile.objects.all())

    class Meta:
        model = CommonRegistrationForm
        fields = ['short_address', 'street_address', 'city', 'state', 'pincode', 'category', 'last_school_name', 'last_school_board', 'last_school_address', 'last_school_class', 'transfer_certificate', 'report_card', 'reason_of_leaving', 'extra_questions', 'last_school_result_percentage', 'transfer_number', 'transfer_date', 'latitude', 'longitude', 'email', 'phone_no', 'single_child', 'first_child',
                  'single_parent', 'first_girl_child', 'staff_ward', 'sibling1_alumni_name', 'sibling1_alumni_school_name', 'sibling1_alumni_proof', 'sibling2_alumni_name', 'sibling2_alumni_school_name', 'sibling2_alumni_proof', 'single_parent_proof', 'family_photo', 'distance_affidavit', 'baptism_certificate', 'parent_signature_upload', 'mother_tongue', 'differently_abled_proof', 'transport_facility_required', "caste_category_certificate", "is_twins", "second_born_child", "third_born_child" ]


class ParentForm(forms.ModelForm):
    alumni_school_name = forms.ModelChoiceField(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
            required=False,
            queryset=SchoolProfile.objects.filter(is_verified=True, is_active=True))
    date_of_birth = forms.DateField(widget=forms.DateInput(format = '%d/%m/%Y'),
                                 input_formats=('%d/%m/%Y',))
    
    class Meta:
        model = ParentProfile
        fields = ['name','phone','email','date_of_birth','gender','photo','income','street_address','city','state','pincode','education','occupation','office_address','office_number','alumni_school_name','alumni_year_of_passing','passing_class','alumni_proof',"transferable_job", "special_ground","companyname", "designation", "profession", "special_ground_proof","pan_card_proof"]

class ChildForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(format = '%d/%m/%Y'),
                                 input_formats=('%d/%m/%Y',))
    class Meta:
        model = Child
        fields = ['name','photo','date_of_birth','gender','religion','nationality','blood_group','birth_certificate','address_proof','address_proof2','first_child_affidavit','minority_proof','vaccination_card','armed_force_proof','aadhaar_card_proof','is_christian','minority_points','student_with_special_needs_points','armed_force_points','orphan']

class SchooolApplicationEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SchooolApplicationEditForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['readonly'] = True
        self.fields['non_collab_receipt'].widget.attrs['readonly']=False
    class Meta:
        model = SchoolApplication
        fields = ['non_collab_receipt','calculated_distance','total_points','distance_points','single_child_points','siblings_studied_points','parents_alumni_points','staff_ward_points','first_born_child_points','transport_facility_points','first_girl_child_points','single_girl_child_points','christian_points','girl_child_point','single_parent_point','minority_points','student_with_special_needs_points','children_of_armed_force_points']

class SchoolProfileForm(forms.ModelForm):
    class Meta:
        model = SchoolProfile
        fields = ['name','email','phone_no','website','school_timings','school_type','school_board','medium','academic_session','school_format','street_address','city','region','state','zipcode','year_established','school_category','ownership','description','student_teacher_ratio','form_price','convenience_fee']

class SchoolPointForm(forms.ModelForm):
    class Meta:
        model = SchoolPoint
        fields = ['single_child_points','siblings_points','parent_alumni_points','staff_ward_points','first_born_child_points','first_girl_child_points','transport_facility_points','single_girl_child_points','is_christian_points','girl_child_points','single_parent_points','minority_points','student_with_special_needs_points','children_of_armed_force_points']


class AgeCriteriaForm(forms.ModelForm):
    
    class Meta:
        model = AgeCriteria
        fields = ['class_relation','start_date','end_date']
        widgets = {
            'start_date': DatePickerInput(format='%Y-%m-%d'), # default date-format %m/%d/%Y will be used
            'end_date': DatePickerInput(format='%Y-%m-%d'), # specify date-frmat
        }

class DistancePointForm(forms.ModelForm):
    class Meta:
        model = DistancePoint
        fields = ['start','end','point']


class ApplicationStatusEditForm(forms.ModelForm):

    class Meta:
        model = ApplicationStatusLog
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(ApplicationStatusEditForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        rank=ApplicationStatusLog.objects.filter(application=initial['pk']).latest('timestamp').status.rank
       
        self.fields['status'].queryset = ApplicationStatus.objects.filter(rank__gt=rank,type='N')
