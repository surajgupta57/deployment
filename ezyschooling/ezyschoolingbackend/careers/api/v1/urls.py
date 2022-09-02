from django.urls import path

from . import views

app_name = "careers"
urlpatterns = [
    path("", views.JobProfileView.as_view(),name="job_list"),
    path("<int:pk>/",views.JobProfileDetailView.as_view(),name="job_detail"),
    path("apply/", views.AppliedProfileView.as_view(),name="job_apply"),
    path("experience/", views.ExperienceListView.as_view(),name="experience_list"),
    path("location/", views.LocationListView.as_view(),name="experience_list"),
    path("joiningtype/", views.JobJoiningTypeListView.as_view(),name="joining_type_list"),
    path("jobdomain/", views.JobDomainListView.as_view(),name="job_domain_list"),

]
