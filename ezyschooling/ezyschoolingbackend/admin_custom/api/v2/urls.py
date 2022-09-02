from django.urls import path

from . import views

app_name = "admin_custom2"
urlpatterns = [
    path("all-user-list/", views.AllUserListCounsellor.as_view(), name="all-user-list"),
    path("all-parent-call-scheduled-list/", views.AllCallScheduldByParentListCounsellor.as_view(), name="all-parent-call-scheduled-list"),
    path("all-unassigned-parent-call-scheduled-list/", views.AllUnassignedCallScheduledByParentListCounsellor.as_view(), name="all-parent-call-scheduled-list"),
    path("all-enquiry-list/", views.AnonymousSchoolEnquiryList.as_view(), name="all-enquiry-list"),
    path("past-user-list/", views.PastUserList.as_view(), name="all-past-user-list"),
    path("past-enquiry-list/", views.PastEnquiryList.as_view(), name="all-past-enquiry-list"),
    path("past-parent-call-scheduled-list/", views.PastCallScheduldByParentList.as_view(), name="all-past-parent-call-scheduled-list"),
    path("children-phone-list/<int:id>/", views.ChildAndPhoneListFromUser.as_view(), name="children-list"),
    path("details/<int:id>/", views.ItemDetailView.as_view(), name="details-item-wise"),
    path("counsellor-filter-data/",views.CounsellorFilterData.as_view(),name='filter-data'),
    path("comment/<int:id>/create/", views.CommentSectionCreateView.as_view(),name='comment-create'),
    path("comment/school/<int:id>/create-list/", views.SchoolCommentSectionCreateRetriveView.as_view(),name='comment-create'),
    path("lead/<int:id>/generate/", views.LeadGeneratedCreateUpdateView.as_view(),name='leade-create-update'),
    path("visit/<int:id>/schedule/", views.VisitScheduleDataCreateUpdateView.as_view(),name='visit-schedule-create-update'),
    path("admission/<int:id>/done/", views.AdmissionDoneDataCreateUpdateView.as_view(),name='admission-done-create-update'),
    path("action/<int:id>/", views.CounselingActionView.as_view(),name='action-view'),
    path("school/action/<int:id>/", views.SchoolActionView.as_view(),name='school-action-view'),
    path("action-list/", views.ActionListView.as_view(),name='action-list'),
    path("school-action-list/", views.SchoolActionListView.as_view(),name='school-action-list'),
    path("school-enquiry-list/", views.SchoolDashboardEnquiryList.as_view(),name='school enquiry list'),
    path("school-past-enquiry-list/", views.SchoolDashboardPastEnquiryList.as_view(),name='school enquiry list'),
    path("counsellor-wise-school-list/", views.CounsellorWiseSchoolList.as_view(),name='counsellor-wise-school-list'),
    path("call-record/<int:id>/", views.CallReocrdView.as_view(),name='call_record'),
    path("counsellor/analytics/<int:id>/", views.AdminSideCounsellorDataView.as_view(), name='counsellor_wise_analytics'),
    path("counsellor/self/analytics/", views.AdminSideCounsellorSelfDataView.as_view(), name='counsellor_wise_analytics'),
    path("analytics/", views.AdminSideAnalyticsDataView.as_view(), name='analytics'),
    path("search/parent-by-number/", views.SearchByPhoneNumberUserList.as_view(), name='search parent by number'),
    path("school/<slug:slug>/<slug:type>/list/", views.SchoolWiseList.as_view(), name='school_data_list'),
    path("school/<slug:slug>/<slug:type>/past-list/", views.SchoolPastDataList.as_view(), name='school_past_data_list'),
    path("get-counsellor_cities/", views.GetCounsellorCityListView.as_view(), name='parent_call_scheduled'),
    path("get-database-inside-school-counts/", views.GetAllSchoolsDetailCountView.as_view(), name='parent_call_scheduled'),
    path("get-database-inside-citywise-school-counts/", views.GetAllCitywiseSchoolsDetailCountView.as_view(), name='parent_call_scheduled'),
    path("database-inside-school-list/", views.DatabaseInsideSchoolsListView.as_view(), name='school-list-db'),
    path("<slug:slug>/admission-open-classes/<int:pk>/", views.DatabaseAdmissionOpenClassesDetailView.as_view(),
         name="school_admission_open_classes_detail_api_view"),
    path("<slug:slug>/admission-open-classes/", views.DatabaseAdmissionOpenClassesView.as_view(),
         name="school_admission_open_classes_api_view"),
    path("<slug:slug>/admission-form-fee/create/", views.DatabaseSchoolAdmissionFormFeeCreateView.as_view(),
         name="school_admission_form_fee_create_api_view"),
    path("search/", views.DatabaseSearchView.as_view(),
         name="school_admission_form_fee_create_api_view"),
    path("upload-school/", views.UploadDataForSchoolProfileView.as_view(),
         name="upload_school"),
    path("create-school-user/", views.DatabaseSchoolRegisterView.as_view(),
         name="upload_school"),
    path("on-process-uploading-status/", views.UploadDataProgressStatusView.as_view(),
         name="on-process-uploading-status"),
    path("404-500-response-list/", views.Response404And500View.as_view(),
         name="on-process-uploading-status"),
    path("parent-call-scheduled/", views.ParentCallScheduledView.as_view(), name='parent_call_scheduled'),
    path("parent-call-scheduled/<int:id>/", views.ParentCallScheduledView.as_view(), name='parent_call_scheduled'),
    path("get-counsellor_cities/", views.GetCounsellorCityListView.as_view(), name='parent_call_scheduled'),
    path("get-time-slot/", views.TimeSlotView.as_view(), name='get-time-slot'),
    path("<slug:slug>/features/", views.DatabaseSchoolFeatureApiView.as_view(), name="features"),
    path("<slug:slug>/fee-structure/", views.DatabaseFeeStructureView.as_view(),
         name="school_fee_structure_api_view"),
    path("counselor-list/", views.CounselorListView.as_view(), name="counselor_list"),
    path("shared-transfer-counselor/<str:type>/", views.SharedTransferredCounselorView.as_view(), name="shared_transferred_counselor"),

]
