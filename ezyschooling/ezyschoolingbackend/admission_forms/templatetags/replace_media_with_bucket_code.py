from django import template

register = template.Library()

@register.filter
def replace_media_with_bucket_code(value):
    return value.replace("/media/","https://ezyschooling-1.s3.amazonaws.com/")
