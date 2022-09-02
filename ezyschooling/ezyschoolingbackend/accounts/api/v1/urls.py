from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
	path("oauth-email-check/", views.CustomGoogleLogin.as_view()),
    path("auth/facebook/", views.FacebookLogin.as_view(), name="facebook_rest_login"),
    path("auth/google/", views.GoogleLogin.as_view(), name="google_rest_login"),
    path("auth/facebook/connect/", views.FacebookConnect.as_view(), name="fb_connect"),
    path("auth/google/connect/", views.GoogleConnect.as_view(), name="google_connect"),
    path("logout/", views.Logout.as_view(), name="rest_logout"),
    path("login/", views.CustomLoginView.as_view(), name="rest_login"),
    path("", views.UserDetailView.as_view(), name="base_user_detail"),
]
