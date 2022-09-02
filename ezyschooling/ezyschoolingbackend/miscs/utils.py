from django.utils.text import slugify


def carousel_image_upload_path(instance, filename):
    return f"carousel/{instance.category.name}/{filename}"


def activity_image_upload_path(instance, filename):
    return f"activity/image/{filename}"


def activity_video_upload_path(instance, filename):
    return f"activity/video/{filename}"


def ezyschooling_new_article_image_upload_path(instance, filename):
    return f"ezyschooling-new-article/{filename}"


def online_event_speaker_image_upload_path(instance, filename):
    speaker = slugify(instance.speaker_name)
    return f"online-events/{speaker}/{filename}"


def principal_pic_upload_path(instance, filename):
    principal = slugify(instance.name)
    return f"schools/gallery/user_{principal}/{filename}"


def user_testimonial_upload_path(instance, filename):
    principal = slugify(instance.name)
    return f"testimonials/user_{principal}/{filename}"

def impactinar_upload_path(instance,filename):
    principal = slugify(instance.title)
    return f"impactinar/{principal}/{filename}"

def employee_img_upload_path(instance, filename):
    principal = slugify(instance.name)
    return f"employee/{principal}/{filename}"
