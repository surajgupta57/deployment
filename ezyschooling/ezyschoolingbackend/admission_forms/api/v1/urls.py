from django.urls import path

from . import views

app_name = "admission_forms"
urlpatterns = [
    path("apply/", views.SchoolApplyView.as_view(), name="school_apply_api_view"),
    path("cart/<int:pk>/", views.ChildSchoolCartDetailView.as_view(),
         name="child_cart_detail_api_view"),
    path("cart/", views.ChildSchoolCartView.as_view(),
         name="child_cart_list_create_api_view"),
    path("cart/total/", views.ChildSchoolCartTotalAmountView.as_view(),
         name="child_cart_total_amount_view"),
    path("cart/update/", views.CartUpdateView.as_view(),name="cart_update_view"),
    path("cart/required-fields/", views.ChildSchoolCartRequiredFieldsView.as_view(), name="child_cart_required_fields_view"
         ),
    path("cart/required-fields-status/", views.ChildSchoolCartRequiredFieldsStatusView.as_view(), name="child_cart_required_fields_status_view"
         ),
    path("applied-school-ids/", views.ChildSchoolApplicationIView.as_view(),
         name="applied_school_ids_api_view"),
    path("<int:pk>/", views.CommonRegistrationFormDetailView.as_view(),
         name="admission_form_detail_api_view"),
    path("form/<int:app_id>/pdf/", views.SchoolApplicationFormPDFDetailView.as_view(),
         name='school_admission_form_pdf'),
    path('alumni-schools-list/', views.AlumniSchoolListView.as_view()),
    path('receipt/<int:app_id>/pdf/', views.SchoolReceiptPDFView.as_view(),
         name='school_receipts'),
    path("points/preference/", views.ChildPointsPreferenceView.as_view()),
    path("points/evaluate/<slug:slug>/", views.ChildPointsEvaluateView.as_view()),
    path("", views.CommonRegistrationFormView.as_view(),
         name="admission_form_list_create_api_view"),
]
