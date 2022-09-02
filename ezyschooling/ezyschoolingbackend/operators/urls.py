from django.urls import path

from .import views

app_name = 'operators'

urlpatterns = [
    path("register/", views.register_view , name="register"),
    path("login/", views.login_view , name="login"),
    path("", views.home_view , name="home"),
    path("logout/",views.logout_view, name="logout"),
    path("delete/<int:pk>/",views.DeleteOperatorView.as_view(),name="delete_operator"),
    path("list/<int:pk>/",views.UpdateOperatorView.as_view(),name="edit_operator"),
    path("list/",views.ListOperatorView.as_view(),name="list"),
    path("<int:pk>/",views.SchoolApplicationTableView.as_view(),name="applications"),
    path("all-applications/",views.AllSchoolApplicationTableView.as_view(),name="all_applications"),
    path('common-form/<int:pk>/',views.CommonFormView.as_view(),name='common_form'),
    path('parent-form/<int:pk>/',views.ParentFormView.as_view(),name='parent_form'),
    path('child-form/<int:pk>/',views.ChildFormView.as_view(),name='child_form'),
    path('applications/<int:pk>',views.schooolApplicationEditView.as_view(),name='school_application_edit_form'),
    path('schools/profile/<int:pk>/',views.SchoolProfileFormView.as_view(),name='school_profile_form'),
    path('schools/point/<int:pk>/',views.SchoolPointFormView.as_view(),name='school_point_form'),
    path('schools/distance/<int:pk>/',views.DistancePointFormView.as_view(),name='school_distance_form'),
    path('schools/create/distance/',views.DistancePointFormCreateView.as_view(),name='school_distance_point_create_form'),
    path('schools/delete/distance/<int:pk>/',views.DistancePointFormDeleteView.as_view(),name='school_distance_point_delete_form'),
    
    path('schools/age/<int:pk>/',views.AgeCriteriaFormView.as_view(),name='school_age_form'),
    path('schools/create/age/',views.AgeCriteriaFormCreateView.as_view(),name='school_age_create_form'),
    path('schools/delete/age/<int:pk>/',views.AgeCriteriaFormDeleteView.as_view(),name='school_age_delete_form'),
    path('schools/<int:pk>/',views.school_dashboard,name='school_dashboard'),
    path('applications/status/<int:pk>',views.ApplicationStatusEditView.as_view(),name='status_edit'),
    path('export/<int:pk>/',views.OperatorExcelExportView.as_view(),name='excel_export'),

]