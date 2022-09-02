from django.urls import path

from miscs.api.v1.views import AdmissionGuidanceCreateView

from . import views

app_name = "miscs"
urlpatterns = [
    path("contact-us/", views.ContactUsView.as_view(), name="contact_us_create"),
    path("carousel-category/", views.CarouselCategoryView.as_view(),
         name="carousel_category"),
    path("carousel/", views.CarouselView.as_view(), name="carousel"),
    path("competition-carousel/", views.CompetitionCarouselView.as_view(),
         name="competition_carousel"),
    path("activity/", views.ActivityView.as_view(), name="activity"),
    path("ezyschooling-news-articles/", views.EzySchoolingNewsArticleView.as_view(),
         name="ezyschooling_news_articles"),
    path("online-events/", views.OnlineEventListView.as_view(), name="online-events"),
    path("achievers/", views.AchieverView.as_view(), name='achievers'),
    path("talent-hunt/", views.TalentHuntSubmissionsView.as_view(),
         name='talenthunt_submissions_list'),
    path("talent-hunt/<slug:slug>/", views.TalentHuntSubmissionsDetailView.as_view(),
         name='talenthunt_submissions_detail'),
    path("talent-hunt/<slug:slug>/like/", views.TalentHuntSubmissionsLikeApiView.as_view(),
         name='talenthunt_like_api_view'),
    path("admission-guidance/", views.AdmissionGuidanceCreateView.as_view(),
         name="admission_guidance_create"),
    path("admission-guidance/slots/", views.AdmissionGuidanceSlotListView.as_view()),
    path("admission-alert/", views.AdmissionAlertView.as_view()),
    path('faq/', views.FaqQuestionView.as_view()),
    path('faq-new/', views.FaqNewQuestionView.as_view()),
    path("admission-guidance-programme/",views.AdmissionGuidanceProgrammeCreateView.as_view()),
    path('survey/create/',views.SurveyResponseCreateView.as_view(),name ="survey_create"),
    path('survey/',views.SurveyListView.as_view(),name="survey"),
    path('survey/check/<int:pk>/',views.CheckSurveyResponseView.as_view(),name="survey_check"),
    path('sponser/',views.SponsorsRegistrationsView.as_view(),name="get_sponser"),
    path('webinar/',views.WebinarRegistrationsView.as_view(),name="webinar_Registraton"),
    path('invitedprincipal/',views.InvitedPrincipalsView.as_view(),name="invited_principal"),
    path('impactinar/',views.PastAndCurrentImpactinarsView.as_view(),name="get_impactinar"),
    path('testimonials/',views.TestimonialView.as_view(),name='testimonials'),
    path('oursponsers/',views.OurSponsers.as_view(),name="sponsers"),
    path('ezyemployees/',views.EzyschoolingEmployeeAPIview.as_view(),name="employee"),
    path('unsubscribe-email/',views.UnsubscribeEmailView.as_view(),name="unsubscribe_email"),
    path('home-page-news-articles/',views.HomePageArticleNews.as_view(),name="home-page-articles-news"),
    # path('drfaq/<slug:slug>/', views.DistrictRegionFAQS.as_view()),

    ]
