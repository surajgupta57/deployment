from django.urls import path

from . import views

app_name = "admin_custom"
urlpatterns = [
    path("sales-executive-list/", views.SalesExecutiveListView.as_view(), name="sales-executive-list"),
    path("city/", views.CACityListView.as_view(), name='city'),
    path("district/", views.CADistrictListView.as_view(), name='district'),
    path("district-region/", views.CADistrictRegionListView.as_view(), name='district_region'),
    path("counselor-executive-list/", views.CounselorExecutiveListView.as_view(), name="counselor-executive-list"),
    path("<int:id>/school-detailed/", views.SchoolDetailedView.as_view(), name="school-detailed-view"),
    path("<int:id>/sales-executive-detail/", views.SalesExecutiveDetailView.as_view(),
         name="sales-executive-detail-view"),
    path("<int:id>/assign-schools/", views.AssignSchoolsView.as_view(), name="assign-schools-view"),
    path("search-schools/", views.SearchSchoolView.as_view(), name="search-school-view"),
    path("", views.CAdminuserProfileView.as_view(), name="custom-admin-user-profile-view"),
    path("<int:id>/school-detail-card-view/", views.SchoolDetailCardView.as_view(), name="school-detail-card-view"),
    path("<int:id>/dashboard-info/", views.DashboardInfoView.as_view(), name="dashboard-info"),
    path("<int:id>/most-visited-schools/", views.MostVisitedSchoolsView.as_view(), name="most-visited-schools"),
    path("<int:id>/school-report-table/", views.SchoolReportTableView.as_view(), name="school-report-table"),
    path("<int:id>/school-detail/", views.SchoolDetailView.as_view(), name="school-detail"),
    path("add-sales-executive/", views.AddSalesExecutive.as_view(), name="add-sales-executive"),
    path("school-profile-filter/", views.SchoolProfileFilterView.as_view(), name="school-profile-filter"),
    path("counselor-executive/", views.CounselorExecutiveView.as_view(), name="CounselorExecutiveView/"),
    path("action-list/", views.ActionSectionView.as_view(), name="action-list"),
    path("users-list/", views.UserListView.as_view(), name="user-list"),
    path("unknown-users-enquiry-data/", views.UnknownUserListView.as_view(), name="unknown_users_enquiry_data"),
    path("unknown-users-enquiry-data/<int:id>/", views.UnknownUsersEnquiryList.as_view(),
         name="unknown_user_enquiry_data"),
    path("children-list/<int:id>/", views.ChildListFromUser.as_view(), name="children-list"),
    path("get-counseling-user-child-data/<int:id>/", views.UserChildDataForCounselingList.as_view(),
         name="get-counseling-user-child-data"),
    path("database-inside-school-list/", views.DatabaseInsideSchoolsListView.as_view(), name='database-inside-school-detail'),
    path("school/<slug:slug>/<slug:type>/<int:id>/viewed-number/", views.ViewedParentPhoneNumberBySchoolView.as_view(),
         name='school_past_data_list'),

]
