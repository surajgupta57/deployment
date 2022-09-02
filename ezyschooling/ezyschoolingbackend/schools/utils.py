import base64
import pyotp
import requests
from django.conf import settings
from django.utils import timezone

def school_activity_image_upload_path(instance, filename):
    return f"school-activity/image/{instance.school.name}/{instance.activity_type.name}/{filename}"


def school_activity_type_slider_images(instance, filename):
    return f"school-activity-type-slider-images/{instance.school.name}/{instance.activity_type.name}/{filename}"

def school_region_photo_upload_path(instance, filename):
    return f"schools/regions/{instance.slug}/{filename}"


def school_country_photo_upload_path(instance, filename):
    return f"schools/country/{instance.slug}/{filename}"

def school_states_photo_upload_path(instance, filename):
    return f"schools/states/{instance.slug}/{filename}"

def school_city_photo_upload_path(instance, filename):
    return f"schools/city/{instance.slug}/{filename}"

def school_district_photo_upload_path(instance, filename):
    return f"schools/district/{instance.slug}/{filename}"

def school_district_region_photo_upload_path(instance, filename):
    return f"schools/districtregion/{instance.slug}/{filename}"

def school_area_photo_upload_path(instance, filename):
    return f"schools/area/{instance.slug}/{filename}"


def school_format_photo_upload_path(instance, filename):
    return f"schools/formats/{instance.slug}/{filename}"


def default_required_admission_form_fields():
    return {
        "single_child": False,
        "first_child": False,
        "single_parent": False,
        "first_girl_child": False,
        "staff_ward": False,
        "sibling1_alumni_name": False,
        "sibling1_alumni_school_name": False,
        "sibling2_alumni_name": False,
        "sibling2_alumni_school_name": False,
        "sibling1_alumni_proof": False,
        "sibling2_alumni_proof": False,
        "family_photo":False,
        "distance_affidavit":False,
        "baptism_certificate":False,
        "parent_signature_upload":False,
        "mother_tongue":False,
        "differently_abled_proof":False,
        "single_parent_proof":False,
        "last_school_name": False,
        "last_school_board": False,
        "last_school_address": False,
        "last_school_class": False,
        "transfer_certificate": False,
        "transfer_number": False,
        "transfer_date": False,
        "lockstatus": False,
        "category": False
    }


def default_required_child_fields():
    return {
        "blood_group": False,
        "birth_certificate": False,
        "address_proof": False,
        "address_proof2":False,
        "first_child_affidavit": False,
        "minority_proof": False,
        "vaccination_card": False,
        "armed_force_proof":False,
        "aadhaar_card_proof":False,
        "is_christian": False,
        "minority_points": False,
        "student_with_special_needs_points": False,
        "children_of_armed_force_points": False,
    }


def default_required_father_fields():
    return {
        "education": False,
        "occupation": False,
        "office_address": False,
        "office_number": False,
        "street_address": False,
        "city": False,
        "state": False,
        "pincode": False,
        "country": False,
        "alumni_school_name": False,
        "alumni_year_of_passing": False,
        "passing_class": False,
        "alumni_proof": False,
        "income": False
    }


def default_required_mother_fields():
    return {
        "education": False,
        "occupation": False,
        "office_address": False,
        "office_number": False,
        "street_address": False,
        "city": False,
        "state": False,
        "pincode": False,
        "country": False,
        "alumni_school_name": False,
        "alumni_year_of_passing": False,
        "passing_class": False,
        "alumni_proof": False,
        "income": False
    }


def default_required_guardian_fields():
    return {
        "education": False,
        "occupation": False,
        "office_address": False,
        "office_number": False,
        "street_address": False,
        "city": False,
        "state": False,
        "pincode": False,
        "country": False,
        "alumni_school_name": False,
        "alumni_year_of_passing": False,
        "passing_class": False,
        "alumni_proof": False,
        "income": False
    }


def school_logo_upload_path(instance, filename):
    return f"schools/logos/user_{instance.user.username}/{filename}"

def school_cover_upload_path(instance, filename):
    return f"schools/cover/user_{instance.user.username}/{filename}"

def alumni_image_upload_path(instance, filename):
    return f"alumni/images/{instance.school.slug}/{filename}"

def boarding_school_infra_image_upload_path(instance, filename):
    return f"schools/boarding/images/{filename}"

def school_gallery_upload_path(instance, filename):
    return f"schools/gallery/user_{instance.school.user.username}/{filename}"

def school_selected_csv_upload_path(instance, filename):
    # print(instance)
    return f"schools/appliedcsv/user_{instance.school_relation.name}/{filename}"

def school_profile_image_upload_path(instance, filename):
   return f"schools/results/images/user_{instance.school.user.username}/{filename}"

def get_year_value_for_seo():
    from schools.models import AdmissionSession
    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1].name.split("-"), AdmissionSession.objects.all().order_by('-id')[:2][0].name.split("-")
    currentSession, nextSession = f"{currentSession[0]}-{currentSession[1][2:]}", f"{nextSession[0]}-{nextSession[1][2:]}"
    return currentSession

def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours, minutes, seconds

def default_boarding_school_faq_value():
    return {"airport_distance":None,"airport_name":None,"airport_cordinates":{"lat":None,"lng":None},"airport_nearby_location":None,"station_distance":None,"station_name":None,"station_cordinates":{"lat":None,"lng":None},"station_nearby_location":None,"laundry_service": True,"guest_house": False, "weather_type":None,"avg_temp":None,"hospital_distance":None,"hospital_name":None,"hospital_cordinates":{"lat":None,"lng":None},"hospital_nearby_location":None,"day_scholar_allowed":False}

def get_boarding_school_faqs(boardingProfile):
    allFAQs = boardingProfile.faq_related_data
    allQuestionAnswer = []
    if allFAQs['airport_name']:
        allQuestionAnswer.append({
            'question':f"Which is the nearest airport to {boardingProfile.extended_school.name}?",
            'answer':f"{allFAQs['airport_name']}, {allFAQs['airport_nearby_location']} is the airport which is nearest to the school. It is situated at a distance of {allFAQs['airport_distance']} from the school.",
        })
    if allFAQs['station_name']:
        allQuestionAnswer.append({
            'question':f"Which is the nearest railway/metro station available?",
            'answer':f"{allFAQs['station_name']}, {allFAQs['station_nearby_location']} is situated at a distance of {allFAQs['station_distance']} from the school",
        })
    if allFAQs['hospital_name']:
        allQuestionAnswer.append({
            'question':f"Which is the nearest hospital to {boardingProfile.extended_school.name}?",
            'answer':f"{allFAQs['hospital_name']}, {allFAQs['hospital_nearby_location']} is the nearest hospital to the school. It is {allFAQs['hospital_distance']} away from the school premises",
        })
    allQuestionAnswer += [
    {
        'question':f"Are laundry services available at the boarding facility?",
        'answer':f"{'Yes, the boarding facility provides laundry services for the students.' if allFAQs['laundry_service'] else 'No, the boarding facility does not provide laundry services, and students are required to manage accordingly.'} {boardingProfile.extended_school.name}.",
    },
    {
        'question':f"Is there a guest house facility available for parents and/or guardians at {boardingProfile.extended_school.name}, {boardingProfile.extended_school.district_region.name}?",
        'answer':f"{'Yes, the school has a guest house facility. You can contact the school to check the availability when visiting your child.' if allFAQs['guest_house'] else 'No, the school does not provide a guest house facility, and you are advised to make arrangements accordingly.'}",
    },
    {
        'question':f"Does the {boardingProfile.extended_school.name} take admissions for day scholars as well?",
        'answer':f"{'Yes, the school welcomes day scholars along with the boarders.' if allFAQs['guest_house'] else 'No, the school does not take admissions for day scholars, and only full-time boarders are allowed.'}",
    }
    ]
    return allQuestionAnswer

def send_sms(phone, message):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID":"1207162247127424387"
    }
    requests.get(url, params=data)

def generate_otp(secret):
    totp = pyotp.TOTP(secret, interval=600)
    return totp.now()

def generate_secret(time, key):
    timestamp = time.astimezone(timezone.get_current_timezone())
    data = f"{str(timestamp)}-{key}"
    data = data.encode("utf-8")
    return base64.b32encode(data)

def verify_otp(secret, code):
    totp = pyotp.TOTP(secret, interval=600)
    return totp.verify(code)

def send_verification_code(enquiry_id):
    from schools.models import SchoolEnquiry
    enq = SchoolEnquiry.objects.get(id=enquiry_id)
    secret = generate_secret(enq.updated_at, settings.SECRET_KEY)
    code = generate_otp(secret)
    print(code)
    print(secret)
    validity = 600 // 60
    message = f"""
    Your OTP for mobile verification is {code}.
    OTP is valid for {validity} minutes and should not be shared with anyone.
    - Ezyschooling Team
    """
    send_sms(enq.second_number, message)

def check_verification_code(enquiry_id, code):
    from schools.models import SchoolEnquiry
    enq = SchoolEnquiry.objects.get(id=enquiry_id)
    secret = generate_secret(enq.updated_at, settings.SECRET_KEY)
    return verify_otp(secret, code)


def remove_unnecessary_json_data(requested_data):
    required_admission_form_fields = requested_data.get('required_admission_form_fields')
    required_child_fields = requested_data.get('required_child_fields')
    required_father_fields = requested_data.get('required_father_fields')
    required_mother_fields = requested_data.get('required_mother_fields')
    required_guardian_fields = requested_data.get('required_guardian_fields')

    import copy

    if 'required_admission_form_fields' in requested_data:
        new_dict = copy.deepcopy(required_admission_form_fields)
        key_name = "required_admission_form_fields"
        for key, val in required_admission_form_fields.items():
            if 'mandatory_' in key:
                new_key = key.replace("mandatory_", "")
                if new_key not in required_admission_form_fields:
                    del new_dict[key]
        requested_data[key_name] = new_dict
        return requested_data
    elif 'required_child_fields' in requested_data:
        new_dict = copy.deepcopy(required_child_fields)
        key_name = "required_child_fields"
        for key, val in required_child_fields.items():
            if 'mandatory_' in key:
                new_key = key.replace("mandatory_", "")
                if new_key not in required_child_fields:
                    del new_dict[key]
        requested_data[key_name] = new_dict
        return requested_data
    elif 'required_father_fields' in requested_data:
        new_dict = copy.deepcopy(required_father_fields)
        key_name = "required_father_fields"
        for key, val in required_father_fields.items():
            if 'mandatory_' in key:
                new_key = key.replace("mandatory_", "")
                if new_key not in required_father_fields:
                    del new_dict[key]
        requested_data[key_name] = new_dict
        return requested_data
    elif 'required_mother_fields' in requested_data:
        new_dict = copy.deepcopy(required_mother_fields)
        key_name = "required_mother_fields"
        for key, val in required_mother_fields.items():
            if 'mandatory_' in key:
                new_key = key.replace("mandatory_", "")
                if new_key not in required_mother_fields:
                    del new_dict[key]
        requested_data[key_name] = new_dict
        return requested_data
    elif 'required_guardian_fields' in requested_data:
        new_dict = copy.deepcopy(required_guardian_fields)
        key_name = "required_guardian_fields"
        for key, val in required_guardian_fields.items():
            if 'mandatory_' in key:
                new_key = key.replace("mandatory_", "")
                if new_key not in required_guardian_fields:
                    del new_dict[key]
        requested_data[key_name] = new_dict
        return requested_data