import os

from django.conf import settings

from .models import ViewedParentPhoneNumberBySchool
from datetime import date

from parents.models import ParentAddress, ParentProfile
from schools.models import SchoolEnquiry, SchoolProfile, FeeStructure, SchoolFeesParameters, SchoolFeesType
from phones.models import PhoneNumber
import pandas as pd

def get_user_phone_numbers(user_id):
    phone_number =[]
    user_parent_profiles = ParentProfile.objects.filter(user__id=user_id)
    for parent_profile in user_parent_profiles:
        if parent_profile.phone:
            if len(parent_profile.phone) == 10:
                phone_number.append(parent_profile.phone)
            elif len(parent_profile.phone) > 10:
                phone_number.append(parent_profile.phone[-10:])
    user_parent_address = ParentAddress.objects.filter(user__id=user_id)
    for parent_address in user_parent_address:
        if parent_address.phone_no:
            if len(parent_address.phone_no) == 10:
                phone_number.append(parent_address.phone_no)
            elif len(parent_address.phone_no) > 10:
                phone_number.append(parent_address.phone_no[-10:])
    user_enquiries = SchoolEnquiry.objects.filter(user__id=user_id)
    for parent_enquiry in user_enquiries:
        if parent_enquiry.phone_no:
            if len(parent_enquiry.phone_no) == 10:
                phone_number.append(parent_enquiry.phone_no)
            elif len(parent_enquiry.phone_no) > 10:
                phone_number.append(parent_enquiry.phone_no[-10:])
    phone_number = set(phone_number)
    return phone_number

def get_user_phone_numbers_for_inside(user_id):
    phone_number =[]
    second_number =[]
    user_parent_profiles = ParentProfile.objects.filter(user__id=user_id)
    for parent_profile in user_parent_profiles:
        if parent_profile.phone:
            if len(parent_profile.phone) == 10:
                phone_number.append(parent_profile.phone)
            elif len(parent_profile.phone) > 10:
                phone_number.append(parent_profile.phone[-10:])
    user_enquiries = SchoolEnquiry.objects.filter(user__id=user_id)
    for parent_enquiry in user_enquiries:
        if parent_enquiry.phone_no:
            if len(parent_enquiry.phone_no) == 10:
                phone_number.append(parent_enquiry.phone_no)
            elif len(parent_enquiry.phone_no) > 10:
                phone_number.append(parent_enquiry.phone_no[-10:])

        if parent_enquiry.second_number and parent_enquiry.second_number_verified:
            if len(parent_enquiry.second_number) == 10:
                second_number.append(parent_enquiry.second_number)
            elif len(parent_enquiry.second_number) > 10:
                second_number.append(parent_enquiry.second_number[-10:])
    user_parent_address = ParentAddress.objects.filter(user__id=user_id)
    for parent_address in user_parent_address:
        if parent_address.phone_no:
            if len(parent_address.phone_no) == 10:
                phone_number.append(parent_address.phone_no)
            elif len(parent_address.phone_no) > 10:
                phone_number.append(parent_address.phone_no[-10:])
    phone_number, second_number = set(phone_number), set(second_number)
    # phone_number = [{"number":item,"valid":False} for item in phone_number]
    for item in second_number:
        if item in phone_number:
            phone_number.remove(item)
        # if item in address_numbers:
        #     address_numbers.remove(item)
    phone_number = [{"number":item,"valid":True} for item in second_number] + [{"number":f"{item.number}","valid":True if item.verified else False} for item in PhoneNumber.objects.filter(user__id=user_id)] + [{"number":item,"valid":False} for item in phone_number]
    return phone_number

def getAllList(dataArray,type, school_id):
    result = []
    for data in dataArray:
        if data.lead:
            item = data.lead
        elif data.visit:
            item = data.visit
        elif data.admissions:
            item = data.admissions
        else:
            pass
        all_field = []
        for field in item._meta.get_fields():
            all_field.append(field.name)
        location = ''
        budget = ''
        classes = ''
        if 'location' in all_field:
            location = item.location
        if 'budget' in all_field:
            budget = item.budget
        if 'classes' in all_field:
            classes = item.classes
        if item.user:
            content_type = 'user'
            number = item.user_phone_number
        elif item.enquiry:
            content_type = 'enquiry'
            number = item.user_phone_number[1:-1]
        elif item.call_scheduled_by_parent:
            content_type = 'Callscheduledbyparent'
            number = item.user_phone_number or item.call_scheduled_by_parent.phone
        school = SchoolProfile.objects.get(id=school_id)
        if type == 'leads':
            viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, lead=item).count()
        elif type == 'visits':
            if ViewedParentPhoneNumberBySchool.objects.filter(school=school, lead__user=item.user).exists():
                viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, lead__user=item.user).count()
            elif ViewedParentPhoneNumberBySchool.objects.filter(school=school, enquiry__user=item.user).exists():
                viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, enquiry__user=item.user).count()
            else:
                viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, visit__user=item.user).count()
        elif type == 'enquiry':
            viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, enquiry=item).count()
        elif type == 'parent_called':
            viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, parent_called=item).count()
        if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
            result.append({
                'id': item.id,
                'name': item.user_name,
                'contact_numbers': number,
                'type': content_type,
                'location': location,
                'budget': budget,
                'classes': classes,
                'timestamp': item.lead_updated_at if str(item._meta).split(".")[
                                                         1] == 'leadgenerated' else item.walk_in_updated_at,
                'viewed': True
            })
        elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
            n = number.replace(" ", "").split(",") if number else []
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
            result.append({
                'id': item.id,
                'name': item.user_name,
                'contact_numbers': hidden_number,
                'type': content_type,
                'location': location,
                'budget': budget,
                'classes': classes,
                'timestamp': item.lead_updated_at if str(item._meta).split(".")[
                                                         1] == 'leadgenerated' else item.walk_in_updated_at,
                'viewed':False
            })

    unique = set()
    unique_result = []
    for obj in result:
        t = tuple(obj.items())
        if t not in unique:
            unique.add(t)
            unique_result.append(obj)
    return unique_result


def create_fee_structure_object(row, session):
    try:
        school = SchoolProfile.objects.get(id=row['School ID'])
        if pd.isna(row['Stream ID']):
            try:
                feestructure, _ = FeeStructure.objects.get_or_create(school=school, class_relation_id=row['Class ID'],session=session)
            except:
                feestructure = FeeStructure.objects.filter(school=school, class_relation_id=row['Class ID'],session=session).first()
        else:
            feestructure, _ = FeeStructure.objects.get_or_create(school=school, class_relation_id=row['Class ID'],stream_relation_id=row['Stream ID'],session=session)
        if feestructure and not feestructure.fee_price:
            feestructure.fee_price = 0
        if not pd.isna(row['Registration Fees']):
            try:
                regfee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=8),tenure=row['Tenure Registration Fees'],price=row['Registration Fees'])
            except:
                regfee = SchoolFeesParameters.objects.filter(school=school,head=SchoolFeesType.objects.get(id=8),tenure=row['Tenure Registration Fees'],price=row['Registration Fees']).first()
            feestructure.fees_parameters.add(regfee)
        if not pd.isna(row['Admission Fee']):
            try:
                addfee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=1), tenure=row['Tenure Admission Fee'],price=row['Admission Fee'])
            except:
                addfee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=1), tenure=row['Tenure Admission Fee'],price=row['Admission Fee']).first()
            feestructure.fees_parameters.add(addfee)
        if not pd.isna(row['Tuition Fees (A)']):
            try:
                tut_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=2),tenure=row['Tenure Tuition Fees (A)'],price=row['Tuition Fees (A)'])
            except:
                tut_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=2),tenure=row['Tenure Tuition Fees (A)'],price=row['Tuition Fees (A)']).first()
            feestructure.fees_parameters.add(tut_fee)
        if not pd.isna(row['Tuition Fees (M)']):
            try:
                tut_fee_m, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=2),tenure=row['Tenure Tuition Fees (M)'],price=row['Tuition Fees (M)'])
            except:
                tut_fee_m = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=2),tenure=row['Tenure Tuition Fees (M)'],price=row['Tuition Fees (M)']).first()
            feestructure.fees_parameters.add(tut_fee_m)
        if not pd.isna(row['Tuition Fees (Q)']):
            try:
                tut_fee_q, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=2),tenure=row['Tenure Tuition Fees (Q)'],price=row['Tuition Fees (Q)'])
            except:
                tut_fee_q = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=2),tenure=row['Tenure Tuition Fees (Q)'],price=row['Tuition Fees (Q)']).first()
            feestructure.fees_parameters.add(tut_fee_q)
        if not pd.isna(row['Security Fees']):
            try:
                sec_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=9), tenure=row['Tenure Security Fees'],price=row['Security Fees'])
            except:
                sec_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=9), tenure=row['Tenure Security Fees'],price=row['Security Fees']).first()
            feestructure.fees_parameters.add(sec_fee)
        if not pd.isna(row['Annual Fees']):
            try:
                annual_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=7), tenure=row['Tenure Annual Fees'],price=row['Annual Fees'])
            except:
                annual_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=7), tenure=row['Tenure Annual Fees'],price=row['Annual Fees']).first()
            feestructure.fees_parameters.add(annual_fee)
        if not pd.isna(row['Development Fees']):
            try:
                dev_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=3),tenure=row['Tenure Development Fees'], price=row['Development Fees'])
            except:
                dev_fee = SchoolFeesParameters.objects.filter(school=school,
                                                                        head=SchoolFeesType.objects.get(id=3),
                                                                        tenure=row['Tenure Development Fees'],
                                                                        price=row['Development Fees']).first()
            feestructure.fees_parameters.add(dev_fee)
        if not pd.isna(row['Other Fees']):
            try:
                other_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=4), tenure=row['Tenure Other Fees'],price=row['Other Fees'])
            except:
                other_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=4), tenure=row['Tenure Other Fees'],price=row['Other Fees']).first()
            feestructure.fees_parameters.add(other_fee)
        if not pd.isna(row['Miscellaneous Charges']):
            try:
                misc_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=5),tenure=row['Tenure Miscellaneous Charges'],price=int(str(row['Miscellaneous Charges']).replace(",","")))
            except:
                misc_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=5),tenure=row['Tenure Miscellaneous Charges'],price=int(str(row['Miscellaneous Charges']).replace(",",""))).first()
            feestructure.fees_parameters.add(misc_fee)
        if not pd.isna(row['Optional Fees']):
            try:
                optn_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=11),tenure=row['Tenure Optional Fees'],price=row['Optional Fees'])
            except:
                optn_fee, _ = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=11),tenure=row['Tenure Optional Fees'],price=row['Optional Fees']).first()
            feestructure.fees_parameters.add(optn_fee)
        if not pd.isna(row['Composite Fees']):
            try:
                compt_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=24),tenure=row['Composite Fees Tenure'],price=row['Composite Fees'])
            except:
                compt_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=24),tenure=row['Composite Fees Tenure'],price=row['Composite Fees']).first()
            feestructure.fees_parameters.add(compt_fee)
        if not pd.isna(row['Transport Fees Start']):
            if not pd.isna(row['Flexible']) and row['Flexible'] == True:
                try:
                    trans_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=15), tenure=row['Tenure Transport Fees'],price=row['Transport Fees Start'],upper_price=row['Transport Fees End'], range=True)
                except:
                    trans_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=15), tenure=row['Tenure Transport Fees'],price=row['Transport Fees Start'],upper_price=row['Transport Fees End'], range=True).first()
            else:
                try:
                    trans_fee, _ = SchoolFeesParameters.objects.get_or_create(school=school, head=SchoolFeesType.objects.get(id=15), tenure=row['Tenure Transport Fees'],price=row['Transport Fees Start'], range=False)
                except:
                    trans_fee = SchoolFeesParameters.objects.filter(school=school, head=SchoolFeesType.objects.get(id=15), tenure=row['Tenure Transport Fees'],price=row['Transport Fees Start'], range=False).first()
            feestructure.fees_parameters.add(trans_fee)
        feestructure.session = session
        feestructure.save()
    except SchoolProfile.DoesNotExist:
        pass


def weekendDays(year, month):
    dt = date(year, month, 1)
    first_week = dt.isoweekday()
    if first_week == 7:
        first_week = 0
    saturday2 = 14 - first_week
    dt2 = date(year, month, saturday2)
    saturday4 = 28 - first_week
    dt4 = date(year, month, saturday4)
    return [dt2.day, dt4.day]

def unique_a_list_of_dict(list):
    new = set()
    new_all_items = []
    for value in list:
        t = tuple(value.items())
        if t not in new:
            new.add(t)
            new_all_items.append(value)
    return new_all_items

from boto3.session import Session

def upload_file_to_bucket(file_path):
    file_dir, file_name = os.path.split(file_path)
    session = Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    s3 = session.resource('s3')
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    bucket_data = s3.Bucket(bucket)

    bucket_data.upload_file(
        Filename=file_path,
        Key=file_name,
        ExtraArgs={'ACL': 'public-read'}
    )

    s3_url = f"https://{bucket}.s3.amazonaws.com/{file_name}"
    return s3_url

