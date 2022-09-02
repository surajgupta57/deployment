from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.views.generic.base import TemplateView
from accounts.api.v1.views import CustomVerifyEmailView

schema_view = get_schema_view(
    openapi.Info(
        title="Ezy Schooling APIS",
        default_version="v1",
        description="Ezyschooling APIS for parenting",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="shekharnunia@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("", include('django.contrib.auth.urls')),
    path("rest-auth/", include("rest_auth.urls")),
    path("admin/", admin.site.urls),
    path("robots.txt",TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("custom-admin/", include("custom_admin.urls",namespace='custom_admin')),
    path('operators/',include("operators.urls")),

    path("taggit/", include("taggit_selectize.urls")),

    path("api/v1/accounts/", include("accounts.api.v1.urls")),
    path("accounts/", include("allauth.urls")),

    path("api/v1/accounts/verify/", CustomVerifyEmailView.as_view(),
         name="account_email_verification_sent"),
    re_path(r"^api/v1/accounts/(?P<key>[-:\w]+)/$", CustomVerifyEmailView.as_view(),
            name="account_confirm_email"),

    path("api/v1/parents/", include("parents.api.v1.urls")),
    path("api/v1/admin_custom/", include("admin_custom.api.v1.urls")),
    path("api/v2/admin_custom/", include("admin_custom.api.v2.urls")),
    path("api/v3/admin_custom/", include("admin_custom.api.v3.urls")),
    path("api/v1/phones/", include("phones.api.v1.urls")),
    path("api/v1/childs/", include("childs.api.v1.urls")),

    path("api/v1/categories/", include("categories.api.v1.urls")),

    path("api/v1/courses/", include("courses.api.v1.urls")),

    path("api/v1/articles/", include("articles.api.v1.urls")),
    path("api/v1/videos/", include("videos.api.v1.urls")),
    path("api/v1/discussions/", include("discussions.api.v1.urls")),
    path("api/v1/tags/", include("tags.api.v1.urls")),

    path("api/v1/news/", include("news.api.v1.urls")),

    path("api/v1/newsletters/", include("newsletters.api.v1.urls")),

    path("api/v1/miscs/", include("miscs.api.v1.urls")),
    path("api/v1/careers/", include("careers.api.v1.urls")),
    path("api/v1/faqs/", include("faqs.api.v1.urls")),
    path("api/v1/elasticdata/", include("ownelasticsearch.api.v1.urls")),
    path("api/v1/experts/", include("experts.api.v1.urls")),
    path("api/v1/payments/", include("payments.api.v1.urls")),
    path("api/v1/analatics/", include("analatics.api.v1.urls")),
    path("api/v1/notifications/", include("notification.api.v1.urls")),
    path("api/v1/admission-forms/", include("admission_forms.api.v1.urls")),
    path("api/v1/schools/", include("schools.api.v1.urls")),
    path("api/v2/schools/", include("schools.api.v2.urls")),
    path("api/v1/admission-informations/articles/",
         include("admission_informations.api.v1.articles.urls")),
    path("api/v1/admission-informations/videos/",
         include("admission_informations.api.v1.videos.urls")),
    path("api/v1/admission-informations/news/",
         include("admission_informations.api.v1.news.urls")),
    path("ckeditor/", include("ckeditor_uploader.urls")),

    path("inbox/notifications/",
         include("notifications.urls", namespace="notifications")),

    path("nested_admin/", include("nested_admin.urls")),  # NEWWWW!!

    path("api/v1/quiz/", include("quiz.api.v1.urls")),
    re_path(
        "swagger(?P<format>\.json|\.yaml)/",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc",
                                       cache_timeout=0), name="schema-redoc"),
    re_path("swagger(?P<format>\.json|\.yaml)/",
            schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/",
         schema_view.with_ui("swagger", cache_timeout=0),
         name="schema-swagger-ui"),
    path("redoc/",
         schema_view.with_ui("redoc", cache_timeout=0),
         name="schema-redoc"),
    path("quiz/email-dashboard/", include("quiz.urls")),
    path("news/email-dashboard/", include("news.urls")),
    path("notification/webpush-dashboard/", include("notification.urls")),
    path("schools/source/", include("schools.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)), ] + urlpatterns

    if "silk" in settings.INSTALLED_APPS:
        urlpatterns = [
            re_path(r"^silk/", include("silk.urls", namespace="silk")),
        ] + urlpatterns


admin.site.site_header = "Ezyschooling Admin"
admin.site.site_title = "Ezyschooling Admin"
admin.site.site_url = "https://ezyschooling.com"
