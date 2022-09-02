from django.utils.text import slugify


def admission_information_article_upload_path(instance, filename):
    return f"admission-information/article/user_{instance.created_by.user.username}/{filename}"


def admission_information_news_thumbnail_upload_path(instance, filename):
    return f"admission-information/news/{filename}"