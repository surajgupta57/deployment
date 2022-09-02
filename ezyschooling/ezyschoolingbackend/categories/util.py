from django.utils.text import slugify

from core.utils import random_string_generator


def board_thumbnail_upload_path(instance, filename):
    return f"boards/{instance.name}/{filename}"


def sub_category_thumbnail_upload_path(instance, filename):
    return f"sub-categorys/{instance.name}/{filename}"

def popup_category_thumbnail_upload_path(instance, filename):
    return f"popup-category/{instance.name}/{filename}"
