from django.urls import path

from . import views

app_name = "quiz"
urlpatterns = [
    path("response/", views.ResponseView.as_view(), name="user_response"),
    path("quiz-takers/", views.QuizTakersView.as_view(), name="quiz_takers"),
    path("sitemap/", views.QuizSitemapData.as_view()),
    path("quiz-category/", views.QuizCategoryView.as_view(), name="quiz_category"),
    path("quiz-category/<slug:slug>/",
         views.QuizCategoryDetailView.as_view(), name="quiz_category_detail"),
    path(
        "quiz-takers/<int:pk>/",
        views.QuizTakersDetailView.as_view(),
        name="quiz_takers_detail",
    ),
    path(
        "quiz-takers/<int:quiztaker_id>/results/",
        views.ResultQuizDetailView.as_view(),
        name="quiz_takers_results_detail",
    ),
    path(
        "quiz-takers/<int:quiztaker_id>/assessment/",
        views.PersonalityAssessmentDetailView.as_view()
    ),
    path("<slug:slug>/related-quiz/",
         views.RelatedQuizView.as_view(), name="related_quiz_list"),
    path("<slug:slug>/", views.QuizDetailView.as_view(), name="quiz_detail"),
    path("", views.QuizView.as_view(), name="quiz_list"),
]
