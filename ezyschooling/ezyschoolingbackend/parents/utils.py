from django.utils.text import slugify

from core.utils import random_string_generator


def parent_profile_picture_upload_path(instance, filename):
    return f"parent/profile_picture/user_{instance.user.username}/{filename}"

def parent_addhar_card_path(instance, filename):
    return f"parent/aadhar_card/user_{instance.user.username}/{filename}"
def parent_pan_card_path(instance, filename):
    return f"parent/pan_card/user_{instance.user.username}/{filename}"

def parent_special_ground_proof(instance, filename):
    return f"parent/special_ground_proof/user_{instance.user.username}/{filename}"
    
def unique_slug_generator(instance, new_slug=None):
    """
    This is for a Django project and it assumes your instance
    has a model with a slug field and a title character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.name)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug, randstr=random_string_generator(size=8)
        )
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug
