from django.urls import path
from . import views

urlpatterns = [
    path("subscribe/", views.WebPushSubscribe.as_view()),
    path("unsubscribe/", views.WebPushUnsubcribe.as_view()),
    path("device-token/", views.DeviceRegistration.as_view()),
    path("whatsapp-subscription/", views.WhatsappSubscriptionView.as_view()),
    path("store-user-city/", views.UserSelectedCityView.as_view(),name='storing_user_city')
]
