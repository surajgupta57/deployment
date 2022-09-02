from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "schools"

router = DefaultRouter()
router.register(r'',
                        views.SchoolDocumentView,
                        basename='schooldocument')

urlpatterns = [
    path("<slug:slug>/ongoing-applications/", views.SchoolOngoingApplicationsListView.as_view(),
         name="school_on_going_applications_list_view"),
    path('<uuid:id>/group-data/',views.GroupedSchoolsView.as_view(),name="grouped_schools_data"),
    path('coupon/', views.CouponView.as_view(),name="coupon-verification-remove"),
    path('<slug:url>/get-all-values/',views.ExploreSchoolURLValues.as_view(),name="get_all_data_for_school_page"),
    path('<slug:url>/validate-url/',views.ExploreSchoolURLValidation.as_view(),name="explore_page_url_validation"),
    path('<uuid:id>/form-details/<slug:uid>/',views.GroupedSchoolsFormView.as_view(),name="grouped_schools_data"),
    path('click-track/',views.ClickAdditionSourceTracking.as_view(),name="click_source_tracking_id"),
    path('trending/', views.TrendingSchoolsHomePage.as_view(), name='home_page_trending_school'),
    path('seo/', views.ExploreSchoolPageSEO.as_view(), name='explore-page-seo'),
    path('avg-fee/', views.SchoolAverageFees.as_view(), name="school_average_fee"),
    path('<slug:slug>/contact-school/', views.SchoolContactClickDataView.as_view(), name="school_profile_contact_click"),
    path('<slug:slug>/alumni/', views.SchoolAlumniView.as_view(), name="school_alumni_list"),
    path('<slug:slug>/boarding-school/', views.BoardingSchoolExtendView.as_view(), name="boarding_school_view"),
    path('<int:id>/day-schedule-deatils/', views.SchoolDayScheduleDetail.as_view(),name='schedule_details'),
    path('<int:id>/infra-deatils/', views.SchoolInfraStructureDetail.as_view(),name='infra_details'),
    path("food-type/", views.FoodOptionsList.as_view(), name='food_type_list'),
    path("infra-head/", views.SchoolInfraHead.as_view(), name='school_infra_head_list'),
    path('<slug:slug>/contact-school/<slug:type>/', views.SchoolContactClickDataRecordView.as_view(), name="school_profile_contact_click_reocrd"),
    path('<slug:slug>/claim-your-skill/', views.ClaimYourSchool.as_view(), name="non_collab_school_claiming"),
    path('<slug:slug>/news-articles/', views.SchoolNewsArticlesView.as_view(), name="school_news_articles"),
    path("<slug:slug>/school-result-image/",views.SchoolAdmissionResultImageView.as_view(),
    name="school-profile-image-view"),
    path("<slug:slug>/school-result-image/<int:pk>/",
    views.SchoolAdmissionResultImageDetailView.as_view(),
    name="school-profile-image-detail-view"),
    path('<slug:slug>/fees-range/',views.school_fee_stucture_min_max_api,name="school_fee_stucture_min_max_api"),
    path("document/", include(router.urls)),
     path("admission-alerts/", views.SchoolAdmissionAlertSubscribeView.as_view(), name="admission-alerts"),
     path("admission-alerts/list/<int:pk>/", views.SchoolSubscribeListView.as_view(), name="admission-alerts-list"),
     path("admission-alerts/delete/<int:pk>/", views.SchoolAdmissionAlertDeleteView.as_view(), name="admission-alerts-delete"),

    path(
        "registration/", views.SchoolRegisterView.as_view(), name="school_registration"
    ),
    path("admission-form-optional-keys/", views.AdmissionFormOptionalKeysView.as_view(),
         name="admission_form_optional_keys"),
    path("applications/", views.SchoolApplicationListView.as_view(),
         name="school_application_list_view"),
    path("applications/excel-export/doe/", views.ExcelExportDOEView.as_view()),
    path("applications/excel-export/all/", views.ExcelExportAllView.as_view()),
    path("applications/<int:pk>/", views.SchoolApplicationDetailView.as_view(),
         name="school_application_list_view"),
     path("applications/status/", views.ApplicationStatusListView.as_view(), name="school_application_status_list_view"),
     path("applications/status/create/", views.ApplicationStatusLogCreateView.as_view(), name="school_application_status_log_create_view"),
    path("code/", views.SchoolCodeFetch.as_view()),
    path('homepage-schools/', views.HomepageSchoolsView.as_view(), name="homepage_schools"),
    path("code/verify/", views.SchoolCodeVerify.as_view()),
    path("code/request/", views.SchoolCodeRequest.as_view()),
    path("featured/", views.FeaturedSchoolListView.as_view()),
    path("sitemap/", views.SchoolProfileSitemapData.as_view()),
    path("city-sitemap/<slug:city>/", views.CityWiseSitemapData.as_view()),
    path("<slug:slug>/school-visitors/",views.SchoolVisitorsDataView.as_view(),name="school_visitors_data"),
    path("<slug:slug>/all-card-data/",views.SchoolCardAllDetailsView.as_view(),name="school_card_all_details"),
    path("<slug:slug>/gallery/<int:pk>/", views.SchoolGalleryDetailView.as_view(),
         name="school_gallery_detail_api_view"),
    path("<slug:slug>/gallery/", views.SchoolGalleryView.as_view(),
         name="school_gallery_api_view"),
    path("<slug:slug>/activity-type/", views.ActivityTypeView.as_view(),
         name="school_activity_type_api_view"),
    path("<slug:slug>/activity-type/<int:pk>/", views.ActivityTypeDetailView.as_view(),
         name="school_activity_type_detail_api_view"),
    path("<slug:slug>/activity/", views.ActivityView.as_view(),
         name="school_activity_create_api_view"),
    path("<slug:slug>/activity/<int:pk>/", views.ActivityDetailView.as_view(),
         name="school_activity_detail_api_view"),

    path("<slug:slug>/fee-structure/", views.FeeStructureView.as_view(),
         name="school_fee_structure_api_view"),

    path("fee-head/",views.FeeHeadDetailViews.as_view(),name="school-fee-head"),
    path("class-streams/",views.FeeStructureStreamsDetailView.as_view(),name="school-class-streams"),
    path("<slug:slug>/fee-structure/<int:pk>/", views.FeeStructureDetailView.as_view(),
         name="school_fee_structure_detail_api_view"),
    path("<slug:slug>/fee_parameter_delet/<int:pk>",views.FeeParameterobjectDelete.as_view(),name="fee_sub_object"),

    path("<slug:slug>/fee-structure/<int:pk>/stream/<int:stream_id>/",
           views.FeeStructureStreamDetailView.as_view()
         ),
    path("<slug:slug>/fee-structure/class/<int:class_id>/",views.FeeStructureClassFilterView.as_view()),


    path("search/", views.SchoolBrowseSearchView.as_view(),
         name="school_search_page"),
    path("school-type/", views.SchoolTypeView.as_view(),
         name="school_schooltype_api_view"),
    path("school-classes/", views.SchoolClassesView.as_view(),
         name="school_classes_api_view"),
    path("activity-autocomplete/", views.ActivityAutocompleteView.as_view()),
    path("activity-type-autocomplete/", views.ActivityTypeAutocompleteView.as_view()),
    path("board/", views.SchoolBoardView.as_view(), name="school_board_api_view"),

    path("format/", views.SchoolFormatView.as_view(), name="school_format_api_view"),

    path("<slug:slug>/views/", views.SchoolViewsListView.as_view(), name="school_views_list_view"),
    path("<slug:slug>/point/create/", views.SchoolPointCreateView.as_view(), name="school_point_create_view"),
    path("<slug:slug>/views/monthly/", views.SchoolViewsMonthWiseView.as_view(), name="school_views_month_wise"),
    path("<slug:slug>/views/export/", views.SchoolViewExcelExport.as_view(), name="school_views_export_view"),
    path("<slug:slug>/point/", views.SchoolPointUpdateView.as_view(),
         name="school_point_api_view"),
    path("<slug:slug>/age-criteria/", views.AgeCriteriaView.as_view(),
         name="school_age_criteria_api_view"),
    path("<slug:slug>/age-criteria/<int:pk>/", views.AgeCriteriaDetailView.as_view(),
         name="school_age_criteria_detail_api_view"),
    path("<slug:slug>/distance-points/", views.DistancePointView.as_view(),
         name="school_distance_point_api_view"),
    path("<slug:slug>/distance-points/<int:pk>/", views.DistancePointDetailView.as_view(),
         name="school_distance_point_detail_api_view"),
    path("<slug:slug>/admission-open-classes/<int:id>/", views.AdmmissionOpenClassesView.as_view(),
         name="school_admission_open_classes_detail_api_view"),
    path("<slug:slug>/admission-open-classes/", views.AdmmissionOpenClassesView.as_view(),
         name="school_admission_open_classes_api_view"),
    path("<slug:slug>/get-admission-open-classes/", views.GetAdmmissionOpenClassesView.as_view(),
         name="school_admission_open_classes_api_view"),
    path("<slug:slug>/", views.SchoolProfileView.as_view(),
         name="school_profile_api_view"),
    path("", views.SchoolBasicProfileView.as_view(),
         name="school_basic_profile_api_view"),
    path("<slug:slug>/enquiry/", views.SchoolEnquiryView.as_view(), name="school_enquiry"),
    path("<slug:slug>/enquiry/export/", views.SchoolEnquiryExcelExport.as_view(), name="school_enquiry_export_view"),
    path("<slug:slug>/form-count/", views.FormsSubmittedWeeklyView.as_view(), name="weekly_form_count"),
    path("<slug:slug>/admission-form-fee/create/", views.SchoolAdmissionFormFeeCreateView.as_view(),
         name="school_admission_form_fee_create_api_view"),
    path("<slug:slug>/admission-form-fee/", views.SchoolAdmissionFormFeeListView.as_view(),
         name="school_admission_form_fee_list_api_view"),
    path("<slug:slug>/upload-csv/",views.SchoolUploadCsvView.as_view(),name="selected_csv"),
    path("<slug:slug>/features/",views.SchoolFeatureApiView.as_view(),name="features"),
    path("<slug:slug>/strfeatures/",views.SchoolFeatureStrApiView.as_view(),name="features_str"),
    path("country",views.CountryView.as_view(),name = "school_country_api_view"),
    path("states",views.StatesView.as_view(),name='school_states_api_view'),
    path("city",views.CityView.as_view(),name='school_city_api_view'),
    path("district",views.DistrictView.as_view(),name='school_districts_api_view'),
    path("districtregion",views.DistrictRegionView.as_view(),name='school_district_region_api_view'),
    path("region", views.RegionView.as_view(), name='school_regions_api_view'),
    path("<slug:slug>/availableclasses/",views.SchoolOpenclassesStatus.as_view(),name="available_classes"),
    path("<slug:slug>/classes/",views.SchoolAvailableClasses.as_view(),name="school_available_classes"),
    path("<slug:slug>/session/",views.SchoolSession.as_view(),name="school_session_detail"),
    path("<slug:slug>/fee-session/",views.SchoolFeeSession.as_view(),name="school_fee_session_detail"),
    path("state/a", views.StateView.as_view(), name="school_state_api_view"),
    path("admission-session", views.AdmissionSessionsView.as_view(), name="school_admission_session_api_view"),
    path("all-admission-session", views.AllAdmissionSessionsView.as_view(), name="school_all_admission_session_api_view"),
    path("explore-school-page", views.AdmissionPageContentView.as_view(), name="admission_page_content"),
    path("<slug:slug>/notify-class/", views.SchoolClassNotificationView.as_view(), name="school_class_notification"),
    path("<slug:slug>/video-tour-links/",views.VideoTourLinksView.as_view(),name="video_tour_link_api_view"),
    path("<slug:slug>/notify-status/",
    views.NotificationStatusView.as_view(), name="school_class_notification_status"),
    path('<int:id>/similar-schools/',views.SimilarSchoolsView.as_view(),name="similar_schools"),
    path('get-multi-class-id/<int:id>/',views.FetchMultiSchoolView.as_view(),name="get_multi_class-id"),
]