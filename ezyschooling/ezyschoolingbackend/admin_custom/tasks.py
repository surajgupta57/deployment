import csv
import os

from celery.decorators import task
from celery.utils.log import get_task_logger
import requests
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string

from .models import AdmissionDoneData, SchoolAction, SchoolPerformedActionOnEnquiry
from schools.models import SchoolProfile, Country, States, City, District, DistrictRegion, SchoolBoard, Pincode, \
    SchoolFormat, SchoolType, Subfeature, Feature, AdmissionSession, BoardingSchoolInfrastructure
import pandas as pd

from .utils import create_fee_structure_object, upload_file_to_bucket

logger = get_task_logger(__name__)
from django.conf import settings
hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD

# lead generated_whatsapp-trigger:
@task(name="lead_generated_whatsapp_trigger")
def lead_generated_whatsapp_trigger(school_phone_number_cannot_viewed, sch_phone_no, parent):
    if not school_phone_number_cannot_viewed:
        phone_number = parent["phone_no"]
    else:
        try:
            n = parent["phone_no"].replace(" ", "").split(",") if parent["phone_no"] else []
        except:
            n = str(parent["phone_no"][0]).replace(" ", "").split(",") if parent["phone_no"] else []
        list2 = []
        if len(n) > 0:
            for a in n:
                list1 = []
                list1[:0] = a
                list1.reverse()
                for index, val in enumerate(list1):
                    if index == 4:
                        break
                    else:
                        list1[index] = 'x'
                list1.reverse()
                hidden_number = ''.join(map(str, list1))
                list2.append(hidden_number)
            hidden_number = ', '.join(map(str, list2))
        else:
            hidden_number = None
        phone_number = hidden_number
    msg_template = f"*Lead generated for your school* 👤\n\nName: {parent['name']}\nPhone: {phone_number}\n\nProcess the lead before it's too late!"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(sch_phone_no) == 10:
        sch_phone_no = "91" + sch_phone_no
    request_body = {
        'method': 'SENDMESSAGE',
        'format': 'json',
        'send_to': sch_phone_no,
        'v': '1.1',
        'isTemplate': True,
        'msg_type': 'TEXT',
        'msg': msg_template,
        'userid': str(hsm_user_id),
        'password': str(hsm_user_password)}
    print(request_body)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    requests.post(endpoint, headers=headers, data=request_body)

# visit_scheduled_whatsapp_trigger:
@task(name="visit_scheduled_whatsapp_trigger")
def visit_scheduled_whatsapp_trigger(school_phone_number_cannot_viewed, sch_phone_no, parent):
    if not school_phone_number_cannot_viewed:
        phone_number = parent["phone_no"]
    else:
        try:
            n = parent["phone_no"].replace(" ", "").split(",") if parent["phone_no"] else []
        except:
            n = str(parent["phone_no"][0]).replace(" ", "").split(",") if parent["phone_no"] else []
        list2 = []
        if len(n) > 0:
            for a in n:
                list1 = []
                list1[:0] = a
                list1.reverse()
                for index, val in enumerate(list1):
                    if index == 4:
                        break
                    else:
                        list1[index] = 'x'
                list1.reverse()
                hidden_number = ''.join(map(str, list1))
                list2.append(hidden_number)
            hidden_number = ', '.join(map(str, list2))
        else:
            hidden_number = None
        phone_number = hidden_number
    msg_template = f"*A walk-in for your school has been scheduled* 🏫\n\nName: {parent['name']}\nPhone: {phone_number}\n\nReach out to the parent in case you need to!"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(sch_phone_no) == 10:
        sch_phone_no = "91" + sch_phone_no
    request_body = {
        'method': 'SENDMESSAGE',
        'format': 'json',
        'send_to': sch_phone_no,
        'v': '1.1',
        'isTemplate': True,
        'msg_type': 'TEXT',
        'msg': msg_template,
        'userid': str(hsm_user_id),
        'password': str(hsm_user_password)}
    print(request_body)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    requests.post(endpoint, headers=headers, data=request_body)


# admission done mail to School heads from inside
@task(name="send_admission_done_mail_to_school_heads")
def send_admission_done_mail_to_school_heads(admission_done_id):
    adm_obj = AdmissionDoneData.objects.get(id=admission_done_id)
    schools = adm_obj.admission_done_for.filter()
    for sch in schools:
        email = sch.head_email_ids.split(',') if sch.head_email_ids else [sch.user.email]
        context = {'parent_name': adm_obj.user_name, 'child_name': adm_obj.child_name}
        message = render_to_string("admission_forms/admission_done_head_mail.html", context)
        send_mail(subject="One new admission done for your school! 👍",
                  message='',
                  html_message=message,
                  from_email='Ezyschooling <info@ezyschooling.in>',
                  recipient_list=[settings.DEFAULT_TO_SCHOOL_EMAIL]+email,
                  connection=settings.EMAIL_CONNECTION, fail_silently=False)


# admission done mail to School heads from School dashboard
@task(name="send_admission_done_mail_to_school_heads_from_school_dashboard")
def send_admission_done_mail_to_school_heads_from_school_dashboard(admission_done_id):
    adm_obj = SchoolPerformedActionOnEnquiry.objects.get(id=admission_done_id)
    school = adm_obj.enquiry.school
    email = school.head_email_ids.split(',') if school.head_email_ids else [school.user.email]
    context = {'parent_name': adm_obj.enquiry.parent_name.title() or adm_obj.user.name.title(), 'child_name': adm_obj.child_name.title()}
    message = render_to_string("admission_forms/admission_done_head_mail.html", context)
    send_mail(subject="One new admission done for your school! 👍",
              message='',
              html_message=message,
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=[settings.DEFAULT_TO_SCHOOL_EMAIL] + email,
              connection=settings.EMAIL_CONNECTION, fail_silently=False)



def remove_space(str):
    str = str.rstrip()
    str = str.lstrip()
    return str

def get_count(count):
    if count > 0:
        return True
    else:
        return False

def get_official_count(official):
    if official > 0:
        return True
    else:
        return False

# upload_school_profiles
@task(name="upload_school_profiles")
def upload_school_profiles(data, db_user, line):
    not_created_schools = []
    for row in data:
        email_id = "query@ezyschooling.com"
        if not row.get('email') or row.get('email') == 'nan':
            email_id = "query@ezyschooling.com"
        else:
            email_id = row.get('email')
        if row.get('description'):
            desc = row.get('description')
        else:
            desc = None
        if row.get('phone_no'):
            phone_no = row.get('phone_no')
        else:
            phone_no = 0
        schoolprofile = SchoolProfile.objects.create(
            user_id=38741,  # default user for development database
            name=row.get('school_name'),
            email=email_id,
            phone_no=phone_no,
            school_timings=row.get('school_timings',None),
            academic_session=row.get('academic_session',None),
            short_address=row.get('short_address',None),
            street_address=row.get('street_address',None),
            ownership="P",
            description=desc,
            is_verified=True,
        )
        try:
            if (pd.isnull(row['school_country_id']) == False):
                country = Country.objects.get(id=row['school_country_id'])
                schoolprofile.school_country = country
            if (pd.isnull(row['school_state_id']) == False):
                state = States.objects.get(id=row['school_state_id'])
                schoolprofile.school_state = state
                count = SchoolProfile.objects.filter(school_state=state).count()
                official = SchoolProfile.objects.filter(collab=True).filter(
                    school_state=state).count()
                state.params = {'School Present': get_count(count), 'Count': count,
                                'Official Present': get_official_count(official),
                                'official_count': official}
                state.save()
            if (pd.isnull(row['school_city_id']) == False):
                city = City.objects.get(id=row['school_city_id'])
                schoolprofile.school_city = city
                count = SchoolProfile.objects.filter(school_city=city).count()
                official = SchoolProfile.objects.filter(collab=True).filter(
                    school_city=city).count()
                city.params = {'School Present': get_count(count), 'Count': count,
                               'Official Present': get_official_count(official),
                               'official_count': official}
                city.save()
            if (pd.isnull(row['district_id']) == False):
                district = District.objects.filter(id=row['district_id']).last()
                schoolprofile.district = district
                count = SchoolProfile.objects.filter(district=district).count()
                official = SchoolProfile.objects.filter(collab=True).filter(
                    district=district).count()
                district.params = {'School Present': get_count(count), 'Count': count,
                                   'Official Present': get_official_count(official),
                                   'official_count': official}
                district.save()
            if (pd.isnull(row['district_region_id']) == False):
                district_region = DistrictRegion.objects.filter(id=row['district_region_id']).last()
                schoolprofile.district_region = district_region
                count = SchoolProfile.objects.filter(district_region=district_region).count()
                official = SchoolProfile.objects.filter(collab=True).filter(
                    district_region=district_region).count()
                district_region.params = {'School Present': get_count(count), 'Count': count,
                                          'Official Present': get_official_count(official),
                                          'official_count': official}
                district_region.save()
                if (pd.isnull(row['Pincode']) == False):
                    pincode, pincode_Created = Pincode.objects.get_or_create(pincode=row['Pincode'])
                    district_region.pincode.add(pincode)
                    district_region.save()
                    schoolprofile.pincode = pincode
            if (pd.isnull(row['school_board']) == False):
                schoolBoard = SchoolBoard.objects.get(name=row['school_board'])
                schoolprofile.school_board = schoolBoard
            if (pd.isnull(row['school_boardss']) == False):
                schoolBoards = SchoolBoard.objects.get(name=row['school_boardss'])
                schoolprofile.school_boardss.add(schoolBoards)
            if (pd.isnull(row['school_format']) == False):
                schoolFormat = SchoolFormat.objects.get(title=row['school_format'])
                schoolprofile.school_format = schoolFormat
            if (pd.isnull(row['school_type']) == False):
                schoolType = SchoolType.objects.get(name=row['school_type']) or None
                schoolprofile.school_type = schoolType
            if (pd.isnull(row['student_teacher_ratio']) == False):
                ratioUpdated = row['student_teacher_ratio'].split(":")
                first = ratioUpdated[0]
                second = ratioUpdated[1]
                if second[0] == "0":
                    second = second[1:]
                ratioUpdated = first + ":" + second
                schoolprofile.student_teacher_ratio = ratioUpdated
            if (pd.isnull(row['school_city']) == False):
                schoolprofile.city = row['school_city']
            if (pd.isnull(row['website']) == False):
                schoolprofile.website = row['website']
            # if (pd.isnull(row['school_state']) == False):
            #     schoolState, _ = State.objects.get_or_create(name=row['school_state'])
            #     schoolprofile.state = schoolState
            if (pd.isnull(row['Pincode']) == False):
                schoolprofile.zipcode = row['Pincode']
            if (pd.isnull(row['year_established']) == False):
                if (row['year_established'] == "NA"):
                    schoolprofile.year_established = ''
                else:
                    year_est = str(int(row['year_established']))
                    schoolprofile.year_established = year_est
            schoolprofile.save()

        except:
            schoolprofile.save()
            not_created_schools.append(schoolprofile.id)

    with open("on_process.txt", "r") as f:
        lines = f.readlines()
    with open("on_process.txt", "w") as f:
        for l in lines:
            if l.strip("\n") != line:
                f.write(l)
        f.write(line.replace("Running", "Done"))

    send_mail(subject="School Uploaded 👍",
              message=f'Hello {db_user["name"]}, Schools which you put on a queue has been uploaded. You can check now in the dashboard. https://inside.ezyschooling.com/database/profile/\n\nBelow schools profile rest data are not added properly. If Empty then no schools pending.\n{not_created_schools}\n\nThanks & Regards,\nTeam Ezyschooling',
              html_message='',
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=[db_user["email"]] + ['ezyschoolingdataupload@gmail.com'],
              connection=settings.EMAIL_CONNECTION, fail_silently=False)


# upload_school_facilities
@task(name="upload_school_facilities")
def upload_school_facilities(data, db_user, line):
    for row in data:
        for i in Subfeature.objects.all():
            name = i.name
            if not pd.isna(row[name]):
                if (Feature.objects.filter(school_id=row['School_id'], features=i).exists()):
                    obj = Feature.objects.get(school_id=row['School_id'], features=i)
                else:
                    school = SchoolProfile.objects.get(id=row['School_id'])
                    obj = Feature.objects.create(school=school, features=i)
            if (row[name]) == True:
                obj.exist = "Yes"
                obj.save()
            if (row[name]) == False:
                obj.exist = "No"
                obj.save()
                
    with open("on_process.txt", "r") as f:
        lines = f.readlines()
    with open("on_process.txt", "w") as f:
        for l in lines:
            if l.strip("\n") != line:
                f.write(l)
        f.write(line.replace("Running", "Done"))
        
    send_mail(subject="School Facilities Uploaded 👍",
              message=f'Hello {db_user["name"]}, Schools facilities which you put on a queue has been uploaded. You can check now in the dashboard. https://inside.ezyschooling.com/database/profile/',
              html_message='',
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=[db_user["email"]] + ['ezyschoolingdataupload@gmail.com'],
              connection=settings.EMAIL_CONNECTION, fail_silently=False)



# upload_district_region
@task(name="upload_district_region")
def upload_district_region(data, db_user, line):
    for row in data:
        try:
            if not Pincode.objects.filter(pincode=row['pincode']).exists():
                Pincode.objects.create(pincode=row['pincode'])
        except:
            pass

    for row in data:
        country_obj = Country.objects.get(id=row['country_id'])
        city_obj = City.objects.get(id=row['city_id'])
        state_obj = States.objects.get(id=row['state_id'])
        if District.objects.filter(id=row['district_id']).exists():
            district_obj = District.objects.get(id=row['district_id'])
        else:
            continue
        new_district_region, _ = DistrictRegion.objects.get_or_create(name=row['district_region_name'],
                                                                      city=city_obj, country=country_obj,
                                                                      state=state_obj, district=district_obj)
        pincode_v = Pincode.objects.get(pincode=row['pincode'])

        if pincode_v not in new_district_region.pincode.all():
            new_district_region.pincode.add(pincode_v)
            new_district_region.save()
            
    with open("on_process.txt", "r") as f:
        lines = f.readlines()
    with open("on_process.txt", "w") as f:
        for l in lines:
            if l.strip("\n") != line:
                f.write(l)
        f.write(line.replace("Running", "Done"))
        
    send_mail(subject="District Region Uploaded 👍",
              message=f'Hello {db_user["name"]}, District Region which you put on a queue has been uploaded. You can check now in the dashboard. https://inside.ezyschooling.com/database/profile/',
              html_message='',
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=[db_user["email"]] + ['ezyschoolingdataupload@gmail.com'],
              connection=settings.EMAIL_CONNECTION, fail_silently=False)


# get_404_500_api_responses
@task(name="get_404_500_api_responses", queue="long-running")
def get_404_500_api_responses(db_user, time, file_name):
    be_sch_list = [{"school id": sch.id, "endpoint": "Profile data missing", "collab": sch.collab, "status": 404}
                   for sch in SchoolProfile.objects.filter(is_active=True, is_verified=True).filter(
            Q(description__isnull=True) | Q(district_region__isnull=True) | Q(school_boardss__isnull=True) | Q(
                school_type__isnull=True)
        )]
    for sch in SchoolProfile.objects.filter(is_verified=True, is_active=True):
        currentSession, nextSession = AdmissionSession.objects.all().order_by('id')[:2][0], \
                                      AdmissionSession.objects.all().order_by('id')[:2][1]

        endpoints = [
            f"https://api.main.ezyschooling.com/api/v2/schools/{sch.slug}/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/fees-range/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/avg-fee/?slug={sch.slug}",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/session",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/news-articles/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/fee-structure/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/fee-head/?limit=50",
            f"https://api.dev.ezyschooling.com/api/v1/schools/admission-session",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/availableclasses/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/classes/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/school-visitors/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/fee-session/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/admission-session",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/school-result-image/",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/school-result-image/",
            f"https://api.dev.ezyschooling.com/api/v2/schools/{sch.slug}/admission-open-classes/?session={currentSession}&class_id=0&child_id=",
            f"https://api.dev.ezyschooling.com/api/v1/schools/{sch.slug}/fee-structure/",
            f"https://api.main.ezyschooling.com/api/v1/schools/{sch.slug}/alumni/?featured=yes",
            f"https://api.main.ezyschooling.com/api/v1/schools/{sch.slug}/boarding-school/",
            f"https://api.main.ezyschooling.com/api/v1/schools/id/infra-deatils/",
        ]
        for i in endpoints:
            if sch.collab:
                if 'infra-deatils' in i:
                    obj = BoardingSchoolInfrastructure.objects.filter(school=sch).last()
                    if obj:
                        i = i.replace("id", obj.id)
                        response = requests.get(f"{i}")
                        if response.status_code == 404 or response.status_code == 500:
                            be_sch_list.append(
                                {"school id": sch.id, "endpoint": i, "collab": sch.collab,
                                 "status": response.status_code})
                    else:
                        pass
                if 'fee-structure' in i:
                    response = requests.get(f"{i}")

                    if response.status_code == 404 or response.status_code == 500:
                        be_sch_list.append({"school id": sch.id, "endpoint": i, "collab": sch.collab,
                                            "status": response.status_code})
                    data = response.json()
                    response = requests.get(f"{i}{data['results'][0]['id']}/")
                    if response.status_code == 404 or response.status_code == 500:
                        be_sch_list.append({"school id": sch.id, "endpoint": i, "collab": sch.collab,
                                            "status": response.status_code})
                    response = requests.get(f"{i}?session={currentSession}")
                    if response.status_code == 404 or response.status_code == 500:
                        be_sch_list.append({"school id": sch.id, "endpoint": i, "collab": sch.collab,
                                            "status": response.status_code})
                else:
                    response = requests.get(f"{i}")
                    if response.status_code == 404 or response.status_code == 500:
                        be_sch_list.append({"school id": sch.id, "endpoint": i, "collab": sch.collab,
                                            "status": response.status_code})
            else:
                if "admission-open-classes" or "fee-structure" or "fees-range" not in i:
                    response = requests.get(f"{i}")
                    if response.status_code == 404 or response.status_code == 500:
                        be_sch_list.append({"school id": sch.id, "endpoint": i, "collab": sch.collab,
                                            "status": response.status_code})

    new_lst = []
    for i in be_sch_list:
        for key, val in i.items():
            if key == 'endpoint':
                if not '/id/infra-deatils' in i[key]:
                    new_lst.append(i)
    fieldnames = ['school id', 'endpoint', 'collab', 'status']
    if len(new_lst) > 0:
        file_path = f"{settings.MEDIA_ROOT}/{file_name}"
        with open(file_path, "w", newline="") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            dict_writer.writeheader()
            dict_writer.writerows(new_lst)
        s3_url = upload_file_to_bucket(file_path)
        send_mail(subject="404 and 500 error page response 👍",
                  message=f'Hello {db_user["name"]}, Data has been generated successfully which you put on a queue on {time}. You can check now by clicking n the link. {s3_url}',
                  html_message='',
                  from_email='Ezyschooling <info@ezyschooling.in>',
                  recipient_list=[db_user["email"]] + ['ezyschoolingdataupload@gmail.com'],
                  connection=settings.EMAIL_CONNECTION, fail_silently=False)

        return s3_url
    else:
        return "0"

# upload_school_fee_structure
@task(name="upload_school_fee_structure")
def upload_school_fee_structure(data, db_user, line):
    for row in data:
        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
        if not pd.isna(row[currentSession.name]) and row[currentSession.name] == True:
            create_fee_structure_object(row, currentSession.name)
        if not pd.isna(row[nextSession.name]) and row[nextSession.name] == True:
            create_fee_structure_object(row, nextSession.name)

    with open("on_process.txt", "r") as f:
        lines = f.readlines()
    with open("on_process.txt", "w") as f:
        for l in lines:
            if l.strip("\n") != line:
                f.write(l)
        f.write(line.replace("Running", "Done"))

    send_mail(subject="School Fee Structure Uploaded 👍",
              message=f'Hello {db_user["name"]}, Schools fee structure which you put on a queue has been uploaded. You can check now in the dashboard. https://inside.ezyschooling.com/database/profile/',
              html_message='',
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=[db_user["email"]] + ['ezyschoolingdataupload@gmail.com'],
              connection=settings.EMAIL_CONNECTION, fail_silently=False)
