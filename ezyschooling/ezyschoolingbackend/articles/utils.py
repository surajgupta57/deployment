from django.utils.text import slugify


def expert_article_upload_path(instance, filename):
    return f"expert-article/user_{instance.created_by.user.username}/{filename}"


def expert_article_audio_upload_path(instance, filename):
    return f"expert-article/user_audio_{instance.created_by.user.username}/{filename}"

