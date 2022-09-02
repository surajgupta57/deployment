from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *

urlpatterns = [
    path('<int:child_id>/order/', CreateOrderView.as_view()),
    path('<int:child_id>/capture/', CaptureTransactionView.as_view()),
    path('admission-guidance-programme/order/',CreateAdmissionGuidanceProgrammeOrderView.as_view()),
    path('admission-guidance-programme/capture/', CaptureAdmissionGuidanceProgrammeTransactionView.as_view()),
    path('admission-guidance/capture/', CaptureAdmissionGuidanceTransactionView.as_view()),
]