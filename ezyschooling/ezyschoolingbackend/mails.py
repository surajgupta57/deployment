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
from schools.models import (
    SchoolEnquiry,
    SchoolClassNotification,
    SchoolProfile,
    City,
    AdmmissionOpenClasses,
)
from django.template.loader import render_to_string
from core.utils import unique_slug_generator_using_name
import requests


def send_logged_in_sms(phone, message):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID": "1207163877792597865",
    }
    requests.get(url, params=data)


def send_fff_sms(phone, message):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID": "1207163895642062771",
    }
    requests.get(url, params=data)


def send_atc_sms(phone, message):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID": "1207163894530255711",
    }
    requests.get(url, params=data)


def send_10_nov_07_jan_user_mails():
    all_users = User.objects.all()

    for user in all_users:
        childs_form_results = []
        # checking if user is parent or not
        if user.is_parent and user.email:
            # Checking if user have any child profile associated with it
            if Child.objects.filter(user=user).exists():
                # print("User has child")
                all_child = Child.objects.filter(user=user)

                for child in all_child:
                    child_data_complete = True
                    mother_data_complete = True
                    father_data_complete = True
                    guardian_data_complete = True
                    form_data_complete = True
                    # Checking if user have any item in the cart for the child
                    if ChildSchoolCart.objects.filter(child=child).exists():
                        # Creating Dictionary of with the filed which are required by default
                        # Required Common Registration Form fields
                        required_admission_form_fields_union = {
                            "short_address": True,
                            "street_address": True,
                            "city": True,
                            "state": True,
                            "pincode": True,
                            "country": True,
                        }
                        # Required Child Profile fileds
                        required_child_fields_union = {
                            "religion": True,
                            "nationality": True,
                            "photo": True,
                        }
                        # Required Father Profile fileds
                        required_father_fields_union = {
                            "email": True,
                            "name": True,
                            "date_of_birth": True,
                            "phone": True,
                            "photo": True,
                        }
                        # Required Mother Profile fileds
                        required_mother_fields_union = {
                            "email": True,
                            "name": True,
                            "date_of_birth": True,
                            "phone": True,
                            "photo": True,
                        }
                        # Required Guardian Profile fileds
                        required_guardian_fields_union = {
                            "email": True,
                            "name": True,
                            "date_of_birth": True,
                            "phone": True,
                            "photo": True,
                        }
                        # getting all the cart item for the child
                        all_cart = ChildSchoolCart.objects.filter(child=child)
                        for cart_item in all_cart:
                            # making union of all the required fields
                            required_admission_form_fields_union = dict(
                                required_admission_form_fields_union,
                                **cart_item.school.required_admission_form_fields,
                            )
                            required_child_fields_union = dict(
                                required_child_fields_union,
                                **cart_item.school.required_child_fields,
                            )
                            required_father_fields_union = dict(
                                required_father_fields_union,
                                **cart_item.school.required_father_fields,
                            )
                            required_mother_fields_union = dict(
                                required_mother_fields_union,
                                **cart_item.school.required_mother_fields,
                            )
                            required_guardian_fields_union = dict(
                                required_guardian_fields_union,
                                **cart_item.school.required_guardian_fields,
                            )
                        # Checking if child have a ommon registration form for it
                        if CommonRegistrationForm.objects.filter(child=child).exists():
                            form = CommonRegistrationForm.objects.get(child=child)
                            # checking if child is orphan or not
                            # if child is not orphan
                            if not child.orphan:
                                # checking if form have father and mother details
                                if form.father and form.mother:
                                    # Checking if child data is complete or not
                                    for data in required_child_fields_union.keys():
                                        if child_data_complete == True:
                                            for key, value in child.__dict__.items():
                                                if data == key and value == None:
                                                    child_data_complete = False
                                                    break
                                    # Checking if father data is complete or not
                                    for data in required_father_fields_union.keys():
                                        if father_data_complete == True:
                                            for (
                                                key,
                                                value,
                                            ) in form.father.__dict__.items():
                                                if data == key and value == None:
                                                    father_data_complete = False
                                                    break
                                    # Checking if mother data is complete or not
                                    for data in required_mother_fields_union.keys():
                                        if mother_data_complete == True:
                                            for (
                                                key,
                                                value,
                                            ) in form.mother.__dict__.items():
                                                if data == key and value == None:
                                                    mother_data_complete = False
                                                    break
                                    # Checking if form data is complete or not
                                    for (
                                        data
                                    ) in required_admission_form_fields_union.keys():
                                        if form_data_complete == True:
                                            for key, value in form.__dict__.items():
                                                if data == key and value == None:
                                                    form_data_complete = False
                                                    break
                                    if (
                                        child_data_complete
                                        and mother_data_complete
                                        and father_data_complete
                                        and form_data_complete
                                    ):
                                        childs_form_results.append("Complete")
                                    else:
                                        childs_form_results.append("Incomplete")

                                else:
                                    # if father or mother profile is not connected
                                    if not form.father:
                                        father_data_complete = False
                                    if not form.mother:
                                        mother_data_complete = False
                            # if child is orphan
                            else:
                                # checking if form have guardian details
                                if form.guardian:
                                    # Checking if child data is complete or not
                                    for data in required_child_fields_union.keys():
                                        if child_data_complete == True:
                                            for key, value in child.__dict__.items():
                                                if data == key and value == None:
                                                    child_data_complete = False
                                                    break
                                    # Checking if guardian data is complete or not
                                    for data in required_guardian_fields_union.keys():
                                        if guardian_data_complete == True:
                                            for (
                                                key,
                                                value,
                                            ) in form.guardian.__dict__.items():
                                                if data == key and value == None:
                                                    guardian_data_complete = False
                                                    break
                                    # Checking if form data is complete or not
                                    for (
                                        data
                                    ) in required_admission_form_fields_union.keys():
                                        if form_data_complete == True:
                                            for key, value in form.__dict__.items():
                                                if data == key and value == None:
                                                    form_data_complete = False
                                                    break

                                    if (
                                        child_data_complete
                                        and guardian_data_complete
                                        and form_data_complete
                                    ):
                                        childs_form_results.append("Complete")
                                    else:
                                        childs_form_results.append("Incomplete")
                                else:
                                    guardian_data_complete = False

                    # If user have any item for the child in cart
                    else:
                        mail_to_be_sent = "LoggedIn"

            # Checking if user doesn't have any child profile associated with it sending Logged in mail
            else:
                mail_to_be_sent = "LoggedIn"

        if user.is_parent and user.email:

            # checking if user is parent or not
            if not childs_form_results:
                email = user.email.lower()
                # if user doesn't have any child form data sending logged in mail
                # Checking if user was logged in b/w a range or not
                if user.last_login:
                    start_date, last_date = datetime.date(2021, 11, 9), datetime.date(
                        2022, 1, 7
                    )
                    if (
                        user.last_login.date() > start_date
                        and user.last_login.date() < last_date
                    ):
                        if user.name:
                            name = user.name
                        else:
                            name = "Parents"
                        sessionV = requests.get(
                            "https://api.main.ezyschooling.com/api/v1/schools/admission-session"
                        )
                        currentSession = sessionV.json()["results"][0]["name"]
                        nextSession = sessionV.json()["results"][1]["name"]
                        parent_address = ParentAddress.objects.get(user=user)
                        city_slug = []
                        for city in City.objects.all():
                            city_slug.append(city.slug)
                        if parent_address.region.slug in city_slug:
                            parent_city = parent_address.region.slug
                        elif (
                            unique_slug_generator_using_name(parent_address.parent.city)
                            in city_slug
                        ):
                            parent_city = unique_slug_generator_using_name(
                                parent_address.parent.city
                            )
                        else:
                            parent_city = "delhi"
                        allSchools = (
                            SchoolProfile.objects.filter(school_city__slug=parent_city)
                            .filter(collab=True)
                            .order_by("-region_rank")
                        )
                        nestedResponse = []
                        i = 1
                        for item in allSchools:
                            if i <= 4:
                                if (
                                    AdmmissionOpenClasses.objects.filter(
                                        school=item,
                                        admission_open="OPEN",
                                        session=currentSession,
                                    ).exists()
                                    or AdmmissionOpenClasses.objects.filter(
                                        school=item,
                                        admission_open="OPEN",
                                        session=nextSession,
                                    ).exists()
                                ):
                                    i += 1
                                    nestedSchool = {}
                                    nestedSchool["id"] = item.id
                                    nestedSchool["name"] = item.name
                                    nestedSchool["slug"] = item.slug
                                    nestedSchool[
                                        "district_region"
                                    ] = item.district_region.name
                                    nestedSchool["district"] = item.district.name
                                    nestedSchool["logo"] = item.logo.url
                                    nestedSchool["description"] = item.description
                                    nestedResponse.append(nestedSchool)
                        message = render_to_string(
                            "parents/logged_in_user_mail.html",
                            {"username": name, "school_list": nestedResponse},
                        )
                        send_mail(
                            subject="Welcome to Ezyschooling!",
                            message="",
                            from_email=[settings.DEFAULT_FROM_EMAIL],
                            recipient_list=[email],
                            html_message=message,
                            fail_silently=False,
                        )
            else:
                complete_form_count = childs_form_results.count("Complete")
                incomplete_form_count = childs_form_results.count("Incomplete")
                email = user.email.lower()
                if complete_form_count > 0 and incomplete_form_count > 0:
                    is_fff = True
                    is_atc = True
                    if user.name:
                        name = user.name
                    else:
                        name = "Parents"
                    school_list = ChildSchoolCart.objects.filter(user=user).order_by(
                        "-timestamp"
                    )[:4]
                    latest_added_school = ChildSchoolCart.objects.filter(
                        user=user
                    ).order_by("-timestamp")[:1][0]
                    school_inq = SchoolEnquiry.objects.filter(
                        school=latest_added_school.school
                    ).count()
                    school_inq = SchoolClassNotification.objects.filter(
                        school=latest_added_school.school
                    ).count()
                    intrested_parents = (
                        school_inq + school_inq + (latest_added_school.views * 0.4)
                    )
                    intrested_parents = int(intrested_parents)
                    message = render_to_string(
                        "parents/atc_fff_mail.html",
                        {
                            "username": name,
                            "complete_form_count": complete_form_count,
                            "incomplete_form_count": incomplete_form_count,
                            "school_list": school_list,
                            "intrested_parents": intrested_parents,
                            "is_atc": is_atc,
                            "is_fff": is_fff,
                        },
                    )
                    send_mail(
                        subject="Welcome to Ezyschooling!",
                        message="",
                        from_email=[settings.DEFAULT_FROM_EMAIL],
                        recipient_list=[email],
                        html_message=message,
                        fail_silently=False,
                    )
                    print("Sending FFF+ATC Mail")
                elif complete_form_count > 0 and incomplete_form_count == 0:
                    is_fff = True
                    is_atc = False
                    if user.name:
                        name = user.name
                    else:
                        name = "Parents"
                    school_list = ChildSchoolCart.objects.filter(user=user).order_by(
                        "-timestamp"
                    )[:4]
                    latest_added_school = ChildSchoolCart.objects.filter(
                        user=user
                    ).order_by("-timestamp")[:1][0]
                    school_inq = SchoolEnquiry.objects.filter(
                        school=latest_added_school.school
                    ).count()
                    school_inq = SchoolClassNotification.objects.filter(
                        school=latest_added_school.school
                    ).count()
                    intrested_parents = (
                        school_inq + school_inq + (latest_added_school.views * 0.4)
                    )
                    intrested_parents = int(intrested_parents)
                    message = render_to_string(
                        "parents/atc_fff_mail.html",
                        {
                            "username": name,
                            "complete_form_count": complete_form_count,
                            "incomplete_form_count": incomplete_form_count,
                            "school_list": school_list,
                            "intrested_parents": intrested_parents,
                            "is_atc": is_atc,
                            "is_fff": is_fff,
                        },
                    )
                    send_mail(
                        subject="Welcome to Ezyschooling!",
                        message="",
                        from_email=[settings.DEFAULT_FROM_EMAIL],
                        recipient_list=[email],
                        html_message=message,
                        fail_silently=False,
                    )
                    print("Sending FFF Mail")
                elif complete_form_count == 0 and incomplete_form_count > 0:
                    is_fff = False
                    is_atc = True
                    if user.name:
                        name = user.name
                    else:
                        name = "Parents"
                    school_list = ChildSchoolCart.objects.filter(user=user).order_by(
                        "-timestamp"
                    )[:4]
                    latest_added_school = ChildSchoolCart.objects.filter(
                        user=user
                    ).order_by("-timestamp")[:1][0]
                    school_inq = SchoolEnquiry.objects.filter(
                        school=latest_added_school.school
                    ).count()
                    school_inq = SchoolClassNotification.objects.filter(
                        school=latest_added_school.school
                    ).count()
                    intrested_parents = (
                        school_inq + school_inq + (latest_added_school.views * 0.4)
                    )
                    intrested_parents = int(intrested_parents)
                    message = render_to_string(
                        "parents/atc_fff_mail.html",
                        {
                            "username": name,
                            "complete_form_count": complete_form_count,
                            "incomplete_form_count": incomplete_form_count,
                            "school_list": school_list,
                            "intrested_parents": intrested_parents,
                            "is_atc": is_atc,
                            "is_fff": is_fff,
                        },
                    )
                    send_mail(
                        subject="Welcome to Ezyschooling!",
                        message="",
                        from_email=[settings.DEFAULT_FROM_EMAIL],
                        recipient_list=[email],
                        html_message=message,
                        fail_silently=False,
                    )
                    print("Sending ATC Mail")


def send_10_nov_07_jan_user_sms():
    all_users = User.objects.all()

    for user in all_users:
        childs_form_results = []
        # checking if user is parent or not
        if user.is_parent and user.email:
            # Checking if user have any child profile associated with it
            if Child.objects.filter(user=user).exists():
                # print("User has child")
                all_child = Child.objects.filter(user=user)

                for child in all_child:
                    child_data_complete = True
                    mother_data_complete = True
                    father_data_complete = True
                    guardian_data_complete = True
                    form_data_complete = True
                    # Checking if user have any item in the cart for the child
                    if ChildSchoolCart.objects.filter(child=child).exists():
                        # Creating Dictionary of with the filed which are required by default
                        # Required Common Registration Form fields
                        required_admission_form_fields_union = {
                            "short_address": True,
                            "street_address": True,
                            "city": True,
                            "state": True,
                            "pincode": True,
                            "country": True,
                        }
                        # Required Child Profile fileds
                        required_child_fields_union = {
                            "religion": True,
                            "nationality": True,
                            "photo": True,
                        }
                        # Required Father Profile fileds
                        required_father_fields_union = {
                            "email": True,
                            "name": True,
                            "date_of_birth": True,
                            "phone": True,
                            "photo": True,
                        }
                        # Required Mother Profile fileds
                        required_mother_fields_union = {
                            "email": True,
                            "name": True,
                            "date_of_birth": True,
                            "phone": True,
                            "photo": True,
                        }
                        # Required Guardian Profile fileds
                        required_guardian_fields_union = {
                            "email": True,
                            "name": True,
                            "date_of_birth": True,
                            "phone": True,
                            "photo": True,
                        }
                        # getting all the cart item for the child
                        all_cart = ChildSchoolCart.objects.filter(child=child)
                        for cart_item in all_cart:
                            # making union of all the required fields
                            required_admission_form_fields_union = dict(
                                required_admission_form_fields_union,
                                **cart_item.school.required_admission_form_fields,
                            )
                            required_child_fields_union = dict(
                                required_child_fields_union,
                                **cart_item.school.required_child_fields,
                            )
                            required_father_fields_union = dict(
                                required_father_fields_union,
                                **cart_item.school.required_father_fields,
                            )
                            required_mother_fields_union = dict(
                                required_mother_fields_union,
                                **cart_item.school.required_mother_fields,
                            )
                            required_guardian_fields_union = dict(
                                required_guardian_fields_union,
                                **cart_item.school.required_guardian_fields,
                            )
                        # Checking if child have a ommon registration form for it
                        if CommonRegistrationForm.objects.filter(child=child).exists():
                            form = CommonRegistrationForm.objects.get(child=child)
                            # checking if child is orphan or not
                            # if child is not orphan
                            if not child.orphan:
                                # checking if form have father and mother details
                                if form.father and form.mother:
                                    # Checking if child data is complete or not
                                    for data in required_child_fields_union.keys():
                                        if child_data_complete == True:
                                            for key, value in child.__dict__.items():
                                                if data == key and value == None:
                                                    child_data_complete = False
                                                    break
                                    # Checking if father data is complete or not
                                    for data in required_father_fields_union.keys():
                                        if father_data_complete == True:
                                            for (
                                                key,
                                                value,
                                            ) in form.father.__dict__.items():
                                                if data == key and value == None:
                                                    father_data_complete = False
                                                    break
                                    # Checking if mother data is complete or not
                                    for data in required_mother_fields_union.keys():
                                        if mother_data_complete == True:
                                            for (
                                                key,
                                                value,
                                            ) in form.mother.__dict__.items():
                                                if data == key and value == None:
                                                    mother_data_complete = False
                                                    break
                                    # Checking if form data is complete or not
                                    for (
                                        data
                                    ) in required_admission_form_fields_union.keys():
                                        if form_data_complete == True:
                                            for key, value in form.__dict__.items():
                                                if data == key and value == None:
                                                    form_data_complete = False
                                                    break
                                    if (
                                        child_data_complete
                                        and mother_data_complete
                                        and father_data_complete
                                        and form_data_complete
                                    ):
                                        childs_form_results.append("Complete")
                                    else:
                                        childs_form_results.append("Incomplete")

                                else:
                                    # if father or mother profile is not connected
                                    if not form.father:
                                        father_data_complete = False
                                    if not form.mother:
                                        mother_data_complete = False
                            # if child is orphan
                            else:
                                # checking if form have guardian details
                                if form.guardian:
                                    # Checking if child data is complete or not
                                    for data in required_child_fields_union.keys():
                                        if child_data_complete == True:
                                            for key, value in child.__dict__.items():
                                                if data == key and value == None:
                                                    child_data_complete = False
                                                    break
                                    # Checking if guardian data is complete or not
                                    for data in required_guardian_fields_union.keys():
                                        if guardian_data_complete == True:
                                            for (
                                                key,
                                                value,
                                            ) in form.guardian.__dict__.items():
                                                if data == key and value == None:
                                                    guardian_data_complete = False
                                                    break
                                    # Checking if form data is complete or not
                                    for (
                                        data
                                    ) in required_admission_form_fields_union.keys():
                                        if form_data_complete == True:
                                            for key, value in form.__dict__.items():
                                                if data == key and value == None:
                                                    form_data_complete = False
                                                    break

                                    if (
                                        child_data_complete
                                        and guardian_data_complete
                                        and form_data_complete
                                    ):
                                        childs_form_results.append("Complete")
                                    else:
                                        childs_form_results.append("Incomplete")
                                else:
                                    guardian_data_complete = False

                    # If user have any item for the child in cart
                    else:
                        mail_to_be_sent = "LoggedIn"

            # Checking if user doesn't have any child profile associated with it sending Logged in mail
            else:
                mail_to_be_sent = "LoggedIn"

        if user.is_parent and user.email:

            # checking if user is parent or not
            if not childs_form_results:
                email = user.email.lower()
                # if user doesn't have any child form data sending logged in mail
                # Checking if user was logged in b/w a range or not
                if user.last_login:
                    start_date, last_date = datetime.date(2021, 11, 9), datetime.date(
                        2022, 1, 7
                    )
                    if (
                        user.last_login.date() > start_date
                        and user.last_login.date() < last_date
                    ):
                        for userProfile in ParentProfile.objects.filter(user=user):
                            if userProfile.parent_type == "":
                                if userProfile.phone:
                                    phonenumber = userProfile.phone
                                    break
                        message = "Start adding schools to your cart and begin your admissions journey with Ezyschooling. Find the right school for your child. Apply Now - https://bit.ly/3dm8JsC"
                        send_logged_in_sms(phonenumber, message)
            else:
                complete_form_count = childs_form_results.count("Complete")
                incomplete_form_count = childs_form_results.count("Incomplete")
                email = user.email.lower()
                if complete_form_count > 0 and incomplete_form_count > 0:
                    is_fff = True
                    is_atc = True
                    if user.name:
                        name = user.name
                    else:
                        name = "Parents"
                    for userProfile in ParentProfile.objects.filter(user=user):
                        if userProfile.parent_type == "":
                            if userProfile.phone:
                                phonenumber = userProfile.phone
                                break
                    message = f""""
                    "Dear {name},
                    Complete your dream school admission form now with Ezyschooling, limited seats are left. Hurry!
                    Complete now:  https://bit.ly/31rXVH7
                    """
                    send_atc_sms(phonenumber, message)
                    print("Sending FFF+ATC SMS")

                elif complete_form_count > 0 and incomplete_form_count == 0:
                    is_fff = True
                    is_atc = False
                    if user.name:
                        name = user.name
                    else:
                        name = "Parents"
                    for userProfile in ParentProfile.objects.filter(user=user):
                        if userProfile.parent_type == "":
                            if userProfile.phone:
                                phonenumber = userProfile.phone
                                break
                    message = f""""
                    "Dear {name},
                    You have filled your form with Ezyschooling. Submit before your desirable school runs out of limited seats. Hurry up! https://bit.ly/31BHqYG
                    """
                    send_fff_sms(phonenumber, message)
                    print("Sending FFF SMS")

                elif complete_form_count == 0 and incomplete_form_count > 0:
                    is_fff = False
                    is_atc = True
                    if user.name:
                        name = user.name
                    else:
                        name = "Parents"
                    for userProfile in ParentProfile.objects.filter(user=user):
                        if userProfile.parent_type == "":
                            if userProfile.phone:
                                phonenumber = userProfile.phone
                                break
                    message = f""""
                    "Dear {name},
                    Complete your dream school admission form now with Ezyschooling, limited seats are left. Hurry!
                    Complete now:  https://bit.ly/31rXVH7
                    """
                    send_atc_sms(phonenumber, message)
                    print("Sending ATC SMS")
