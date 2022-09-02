import base64
import imghdr
import random
import string
import uuid

import six
from django.core.files.base import ContentFile
from django.utils.text import slugify
from rest_framework import serializers

from backend.logger import info_logger,error_logger

def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator_using_title(instance, new_slug=None):
    """
    This is for a Django project and it assumes your instance
    has a model with a slug field and a title character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug, randstr=random_string_generator(size=8)
        )
        return unique_slug_generator_using_title(instance, new_slug=new_slug)
    return slug


def unique_slug_generator_using_name(instance, new_slug=None):
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
        return unique_slug_generator_using_name(instance, new_slug=new_slug)
    return slug


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
                # print type(decoded_file)
            except TypeError:
                error_logger(f"{self.__class__.__name__} TYPEERROR INVALID IMAGE")
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)
        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension
