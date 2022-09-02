import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

import datetime
from accounts.models import User
from django.core.mail import send_mail
from django.conf import settings
from admission_forms.models import ChildSchoolCart, CommonRegistrationForm
from childs.models import Child
from parents.models import ParentProfile, ParentAddress
from schools.models import SchoolEnquiry, SchoolClassNotification, SchoolProfile, City
from django.template.loader import render_to_string
from core.utils import unique_slug_generator_using_name
import requests
from django.core.mail import get_connection, send_mail
from django.core.mail.message import EmailMessage
school_list = ChildSchoolCart.objects.all().order_by('-timestamp')[:4]

message = render_to_string("parents/atc_fff_mail.html",
                            {'username': "Test Mail",
                            'complete_form_count': 10,
                            'incomplete_form_count':5,
                            'school_list':school_list,
                            'intrested_parents':51,
                            'is_atc':True,
                            'is_fff':True,})

send_mail(subject="Important! Complete your child's admission form with Ezyschooling",
        message='',
        html_message=message,
        from_email='Ezyschooling <info@ezyschooling.in>',
        recipient_list=['himalaya.ezyschooling@gmail.com'],
        connection=settings.EMAIL_CONNECTION, fail_silently=False)
# send_mail(subject="Welcome to Ezyschooling!",
#             message='',
#             from_email='info@ezyschooling.in',
#             recipient_list=['himalaya.ezyschooling@gmail.com'],
#             html_message=message,
#             fail_silently=False)
