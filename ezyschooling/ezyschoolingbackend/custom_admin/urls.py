from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from . import views
from .views import RegionAutocomplete, SchoolAutocomplete
from django.views.generic import TemplateView

app_name = 'custom_admin'

urlpatterns = [
    path('contact-us-anon-data',views.get_contact_us_for_anon_user,name="get_contact_us_for_anon_user"),
    path('schoolenquirydata-for-anon-user',views.get_school_enquiry_for_anon_user,name="get_school_enquiry_for_anon_user"),
    path("get_parent_address_api_data/<user_id>",views.get_parent_address_api_data,name="get_parent_address_api_data"),
    path("get_parent_profile_api_data/<user_id>",views.get_parent_profile_api_data,name="get_parent_profile_api_data"),
    path("get_common_registration_form_api_data/<user_id>",views.get_common_registration_form_api_data,name="get_common_registration_form_api_data"),
    path("get_parent_child_data/<user_id>",views.get_parent_child_data,name="get_parent_child_data"),
    path("get_school_enquiry_api/<user_email>",views.get_school_enquiry_api,name="get_school_enquiry_api"),
    path("get_school_application_api/<user_id>",views.get_school_application_api,name="get_school_application_api"),
    path("contact-us/",staff_member_required(views.get_all_contactus_data),name="contact_us"),
    path("",staff_member_required(views.get_all_parent_profile_data),name="get_all_parent_profile_data"),
    path("school-application-data/",staff_member_required(views.get_all_school_application_data),name="get_all_school_application_data"),
    path("home/", staff_member_required(views.home), name="home"),
    path('get-contact-us-data',staff_member_required(views.get_contactus_graph_data),name = "get_contactus_graph_data"),
    path('get-school-enquiry-graph-data',staff_member_required(views.get_school_enquiry_graph_data),name = "get_school_enquiry_graph_data"),
    path("get-child-school-cart-data",staff_member_required(views.get_all_child_cart_data),name="cart_data"),
    path('cart-graph-data',staff_member_required(views.get_cart_graph_data),name="get_cart_graph_data"),
    path("user-cart",staff_member_required(views.get_all_child_cart_data)),
    path("get_cart_items/<user_id>/",staff_member_required(views.get_cart_items),name="get_cart_items_by_id"),
    path("cart-enquiry/",staff_member_required(views.get_all_parent_profile_data)),
    path("pincodes",staff_member_required(views.get_pincodes),name="get_pincode"),
    path('data/', staff_member_required(views.pivot_data), name='pivot_data'),
    path('monthly/',staff_member_required(views.this_month_analytics),name='this_month_analytics'),
    path('cart/',staff_member_required(views.get_all_child_cart_data),name='user_with_cart'),
    path('admissionguidance/',views.get_all_admission_guidance_data,name='admission_guidance_data'),
    path(
        'user-signup/',
        staff_member_required(
            views.ParentTableView.as_view()),
        name="user_signup"),
    path(
        'form-details/<int:pk>/',
        views.form_details,
        name="form_details"),
    path(
        'all-applications/',
        staff_member_required(
            views.SchoolApplicationTableView.as_view()),
        name="all_applications"),
    path(
        'school-views/',
        staff_member_required(
            views.SchoolViewTableView.as_view()),
        name='school_views'),
    path(
        'school-enquiry/',
        staff_member_required(views.get_all_school_enquiry),
        name='school_enquiries'),
    path(
        'school-autocomplete/',
        SchoolAutocomplete.as_view(),
        name='school-autocomplete'),
    path(
        'region-autocomplete/',
        RegionAutocomplete.as_view(),
        name='region-autocomplete'),
    path(
        'school/<int:id>/',
        staff_member_required(
            views.SchoolDetailView.as_view()),
        name='school_details'),
    path('uniform-app/', views.uniform_app_analysis, name="uniform-app-analysis"),
    path('uniform-app/login/',views.login_view, name="uniform-app-login"),
    path('uniform-app/logout/',views.logout_view, name="uniform-app-logout"),
    path('export_csv/',views.Export,name='excel_export_bulk'),
    path('export_csv_school_enquiry/',views.export_get_school_enquiry_for_anon_user,name='export_get_school_enquiry_for_anon_user'),
    path('export_csv_contact_us/',views.export_get_contact_us_for_anon_user,name="export_get_contact_us_for_anon_user"),
    path('export_csv_admission_guidance/',views.export_csv_admission_guidance,name='export_csv_admission_guidance')
    
]
