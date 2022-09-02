from admission_forms.models import CommonRegistrationForm, SchoolApplication, ApplicationStatusLog, ApplicationStatus
from childs.models import Child
from custom_admin.filters import SchoolApplicationFilter
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, UpdateView, DetailView, CreateView, DeleteView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, SingleTableView
from parents.models import ParentProfile
from .forms import *
from .models import Operator
from .tables import AssignedSchoolsTable, SchoolApplicationTable
from schools.models import SchoolProfile, DistancePoint, AgeCriteria, SchoolPoint, Region
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import csv
from django.http import Http404, HttpResponse
from django_tables2.config import RequestConfig
from .filters import SchoolOperatorFilter,SchoolApplicationOperatorFilter
from django.db.models import Q

def admin_check(user):
    return user.is_staff

def operator_check(user):
    return Operator.objects.filter(user=user).exists()
    
@user_passes_test(admin_check,login_url="/admin/login")
def register_view(request):
    if request.method == 'POST':
        f = UserForm(request.POST)
        if f.is_valid():
            user= f.save()
            schools= f.cleaned_data.pop('school')
            name=f.cleaned_data.pop('name')
            operator= Operator.objects.create(user=user,name=name)
            operator.school.set(schools)
            messages.success(request, 'New Operator has been created',extra_tags='alert-success')
    else:
        f = UserForm()

    return render(request, 'operators/register.html', {'form': f})

class UpdateOperatorView(SuccessMessageMixin,UserPassesTestMixin,UpdateView):
    form_class = OperatorEditForm
    template_name = 'operators/edit_operator.html'
    success_url = '/operators/list'
    success_message = "Operator updated successfully"
    queryset = Operator.objects.all()
    login_url = '/admin/login/'

    def test_func(self):
        return self.request.user.is_staff

def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(request, username=username, password=password)
        if user != None and Operator.objects.filter(user=user).exists():
            login(request, user)
            return redirect("/operators/")
        else:
            messages.error(request, 'Invalid credentials!!',extra_tags='alert-danger')
            return redirect("/operators/login")
    return render(request, "operators/login.html", {"form": form})

@login_required(login_url='/operators/login')
@user_passes_test(operator_check,login_url='/operators/login')
def home_view(request):
    user= request.user
    operator = Operator.objects.get(user=user)
    f = SchoolOperatorFilter(request.GET, queryset=operator.school.all())
    table = AssignedSchoolsTable(f.qs)
    table.paginate(page=request.GET.get("page", 1), per_page=25)
    RequestConfig(request).configure(table)
    context= {'schools':table ,'filter':f,'operator':operator}

    return render(request,"operators/home.html",context)


def logout_view(request):
    logout(request)
    return render(request,"operators/logout.html",{})

class ListOperatorView(UserPassesTestMixin,ListView):
    template_name = 'operators/list.html'
    queryset = Operator.objects.select_related("user").all()
    login_url = '/admin/login/'

    def test_func(self):
        return self.request.user.is_staff


class DeleteOperatorView(UserPassesTestMixin,DeleteView):
    model = Operator
    login_url = '/admin/login/'

    def get_success_url(self):
        return f"/operators/list/"
    
    def test_func(self):
        return self.request.user.is_staff

class SchoolApplicationTableView(SingleTableMixin, FilterView):
    model = SchoolApplication
    table_class = SchoolApplicationTable
    template_name = 'operators/school_applications.html'
    filterset_class = SchoolApplicationOperatorFilter

    def get_queryset(self, **kwargs):
        queryset = SchoolApplication.objects.filter(school=self.kwargs['pk']).select_related(
            "school", "child", "user", "apply_for", "school__region")
        if 'q' in self.request.GET and self.request.GET['q']:
            q = self.request.GET['q']
            queryset = queryset.filter(Q(child__name__icontains=q)|Q(user__name__icontains=q)|Q(school__name__icontains=q))
        
        if 'status' in self.request.GET and self.request.GET['status']:
            status = self.request.GET['status']
            queryset = queryset.filter(Q(status__status__rank=status)).exclude(Q(status__status__rank__gt=status))
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk= self.kwargs.get('pk')
        context["pk"]= pk
        school = SchoolProfile.objects.filter(id=pk).first()
        context["school"]= school.name
        context["website"]= school.website
        context["application_count"]= context['schoolapplication_list'].count()
        context["submitted_to_school_count"]= context['schoolapplication_list'].filter(status__status__rank=3).count()
        context["receipt_generated_count"]= context['schoolapplication_list'].filter(status__status__rank=4).count()
        return context
    
class AllSchoolApplicationTableView(SingleTableMixin, FilterView):
    model = SchoolApplication
    table_class = SchoolApplicationTable
    template_name = 'operators/school_applications.html'
    filterset_class = SchoolApplicationOperatorFilter

    def get_queryset(self):
        operator = Operator.objects.get(user=self.request.user)
        schools= operator.school.all()
        queryset= SchoolApplication.objects.filter(school__in=schools).select_related(
            "school", "child", "user", "apply_for", "school__region")
        if 'q' in self.request.GET and self.request.GET['q']:
            q = self.request.GET['q']
            queryset = queryset.filter(Q(child__name__icontains=q)|Q(user__name__icontains=q)|Q(school__name__icontains=q))

        if 'status' in self.request.GET and self.request.GET['status']:
            status = self.request.GET['status']
            queryset = queryset.filter(Q(status__status__rank=status)).exclude(Q(status__status__rank__gt=status))
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["application_count"]= context['schoolapplication_list'].count()
        context["submitted_to_school_count"]= context['schoolapplication_list'].filter(status__status__rank=3).count()
        context["receipt_generated_count"]= context['schoolapplication_list'].filter(status__status__rank=4).count()
        return context

class CommonFormView(UpdateView):
    form_class= CommonForm
    model = CommonRegistrationForm
    template_name = 'operators/form_details.html'
    success_message = "form updated successfully"

    def get_success_url(self):
        return f"/operators/common-form/{self.kwargs['pk']}"

class ParentFormView(SuccessMessageMixin ,UpdateView):
    form_class= ParentForm
    model = ParentProfile
    template_name = 'operators/parent_details.html'
    success_message = "Parent profile updated successfully"

    def get_success_url(self):
        return f"/operators/parent-form/{self.kwargs['pk']}"

class ChildFormView(UpdateView):
    form_class= ChildForm
    model = Child
    template_name = 'operators/child_details.html'
    success_message = "Child profile updated successfully"

    def get_success_url(self):
        return f"/operators/child-form/{self.kwargs['pk']}"

class schooolApplicationEditView(UpdateView):
    form_class= SchooolApplicationEditForm
    model = SchoolApplication
    template_name = 'operators/edit_school_application.html'
    success_message = "School Application updated successfully"

    def get_success_url(self):
        return f"/operators/applications/{self.kwargs['pk']}"
    
class SchoolProfileFormView(UpdateView):
    form_class= SchoolProfileForm
    model = SchoolProfile
    template_name = 'operators/school_profile.html'
    success_message = "School profile updated successfully"

    def get_success_url(self):
        return f"/operators/schools/profile/{self.kwargs['pk']}"

class AgeCriteriaFormView(UpdateView):
    form_class= AgeCriteriaForm
    model = AgeCriteria
    template_name = 'operators/age_criteria.html'
    success_message = "age criteria updated successfully"

    def get_success_url(self):
        return f"/operators/schools/age/{self.kwargs['pk']}"

class AgeCriteriaFormCreateView(CreateView):
    model = AgeCriteria
    template_name = 'operators/age_criteria.html'
    success_message = "age criteria created successfully"
    fields = '__all__'

    def get_success_url(self):
        return f"/operators/schools/{self.object.school.pk}"

class AgeCriteriaFormDeleteView(DeleteView):
    model = AgeCriteria
    success_message = "age criteria deleted successfully"

    def get_success_url(self):
        return f"/operators/schools/{self.object.school.pk}"

class DistancePointFormView(UpdateView):
    form_class= DistancePointForm
    model = DistancePoint
    template_name = 'operators/distance_point.html'
    success_message = "Distance point updated successfully"

    def get_success_url(self):
        return f"/operators/schools/distance/{self.kwargs['pk']}"


class DistancePointFormCreateView(CreateView):
    model = DistancePoint
    template_name = 'operators/distance_point.html'
    success_message = "distance_point created successfully"
    fields = '__all__'

    def get_success_url(self):
        return f"/operators/schools/{self.object.school.pk}"

class DistancePointFormDeleteView(DeleteView):
    model = DistancePoint
    success_message = "distance_point deleted successfully"

    def get_success_url(self):
        return f"/operators/schools/{self.object.school.pk}"

class SchoolPointFormView (UpdateView):
    form_class= SchoolPointForm
    model = SchoolPoint
    template_name = 'operators/school_point.html'
    success_message = "School point updated successfully"

    def get_success_url(self):
        return f"/operators/schools/point/{self.kwargs['pk']}"

def school_dashboard(request,pk):
    school_profile = SchoolProfile.objects.filter(id=pk).first()
    age_criterias = AgeCriteria.objects.filter(school=pk).select_related("school")
    school_point = SchoolPoint.objects.filter(school=pk).select_related("school").first()
    distance_points = DistancePoint.objects.filter(school=pk).select_related("school")
    context = {'school_profile': school_profile, 'age_criterias': age_criterias,
               'school_point': school_point, 'distance_points': distance_points}

    return render(request,"operators/school_dashboard.html",context)

class ApplicationStatusEditView(CreateView):
    model = ApplicationStatusLog
    template_name = 'operators/status_edit.html'
    success_message = "application status changed successfully"
    form_class= ApplicationStatusEditForm

    def get_success_url(self):
        return f"/operators/applications/status/{self.kwargs['pk']}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = ApplicationStatusLog.objects.filter(application=self.kwargs['pk'])
        context['application']= self.kwargs['pk']
        return context
    
    def get_initial(self):
        return {
            'pk':self.kwargs.get('pk'),
        }

    def form_valid(self, form):
        application = get_object_or_404(SchoolApplication, id=self.kwargs['pk'])
        form.instance.application = application
        response = super(ApplicationStatusEditView, self).form_valid(form)
        return response
    
class OperatorExcelExportView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request,pk, format=None):
        apps = SchoolApplication.objects.select_related(
            "child", "form").filter(school__pk=pk)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="All Forms List.csv"'
        writer = csv.DictWriter(
            response,
            fieldnames=[
                'Form Id',
                'Date Received',
                'Points',
                'Distance Points',
                'Single Child Points',
                'First Born Child Points',
                'Sibling Studied Points',
                'First Girl Child Points',
                'Single Girl Child Points',
                'Staff Ward Points',
                'Name',
                "Applying For",
                "Date of Birth",
                "Child Age",
                'Address',
                'City',
                'State',
                'Zipcode',
                'Gender',
                'Category',
                'Email',
                'Phone No',
                'Blood Group',
                'Religion',
                'Nationality',
                'Father\'s Name',
                'Father\'s Age',
                'Father\'s Phone No',
                'Father\'s Email',
                'Mother\'s Name',
                'Mother\'s Age',
                'Mother\'s Phone No',
                'Mother\'s Email',
                'Father\'s Photo',
                'Mother\'s Photo',
                'Child\'s Photo'
            ]
        )
        writer.writeheader()
        for i in apps:
            writer.writerow({
                'Form Id': i.uid,
                'Date Received': i.timestamp.strftime("%-d/%-m/%Y %-I:%-M%p") or None,
                'Date of Birth': i.child.date_of_birth or None,
                'Name': i.child.name.title() or None,
                "Child Age": i.child.age_str or None,
                'Child\'s Photo': i.child.photo.url or None,
                'Gender': i.child.gender.title() or None,
                'Father\'s Name': i.form.father.name.title() or None,
                'Father\'s Photo': i.form.father.photo.url or None,
                'Father\'s Age': i.form.father.age or None,
                'Father\'s Phone No': i.form.father.phone or None,
                'Father\'s Email': i.form.father.email or None,
                'Mother\'s Name': i.form.mother.name.title() or None,
                'Mother\'s Photo': i.form.mother.photo.url or None ,
                'Mother\'s Age': i.form.mother.age or None,
                'Mother\'s Phone No': i.form.mother.phone or None,
                'Mother\'s Email': i.form.mother.email or None,
                "Applying For": i.apply_for.name or None,
                "Points": i.total_points or None,
                'Address': i.form.street_address or None,
                'Zipcode': i.form.pincode or None,
                'City': i.form.city or None,
                'State': i.form.state or None,
                'Phone No': i.form.father.phone or None,
                'Category': i.form.category or None,
                'Email': i.user.email or None,
                'Blood Group': i.child.blood_group or None,
                'Religion': i.child.religion or None,
                'Nationality': i.child.nationality or None,
                'Distance Points':i.distance_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
                'Single Child Points':i.single_child_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
                'First Born Child Points':i.first_born_child_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
                'Sibling Studied Points':i.siblings_studied_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
                'First Girl Child Points':i.first_girl_child_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
                'Single Girl Child Points':i.single_girl_child_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
                'Staff Ward Points':i.staff_ward_points if(i.apply_for.name in ["Nursery","KG","Class 1"]) else "N/A",
            })
        return response
