from dal import autocomplete
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db import connection
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import DetailView
from django_filters.views import FilterView
from django_tables2.export.views import ExportMixin
from django_tables2.views import SingleTableMixin
from django.contrib.auth import authenticate, login, logout, decorators
from parents.models import ParentProfile
from django.db import connections
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
# from django.db.models import COUNT
from django.db.models.functions import Trunc
from accounts.models import User
# from admission_forms import CommonRegistrationForm
from admission_forms.models import (ChildSchoolCart, CommonRegistrationForm,
                                    SchoolApplication,FormReceipt)
from parents.models import ParentProfile,ParentAddress
from schools.models import Region, SchoolEnquiry, SchoolProfile, SchoolView
from miscs.models import AdmissionGuidance
from accounts.models import User
from django.db import connection
from .filters import *
from .tables import *
from .forms import *
from analatics.models import PageVisited
from rest_framework.decorators import api_view
from django.core import serializers
from rest_framework.response import Response
#from .serializers import CustomUserSerializer
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.db.models.functions import ExtractMonth,ExtractYear,ExtractDay
import datetime

from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
import datetime
from datetime import timedelta
from .query import *
from miscs.models import ContactUs
from django.utils.timezone import localtime
from django.db.models import Prefetch
from django.core.paginator import Paginator
from datetime import datetime as datetime_custom

from childs.models import Child
import csv
from django.http import Http404, HttpResponse

# def get_all_child_cart_data(request):
#     data_list = []
#     '''
#     data = ChildSchoolCart.objects.all().order_by("-timestamp")
#     for i in data:
#         if ParentAddress.objects.filter(parent__user = i.form.user).exists():
#             obj = ParentAddress.objects.get(parent__user = i.form.user)
#             data_list.append((obj,i))
#     '''
#     return render(request,'custom_admin/cart_items_custom.html',{'dataset':data_list})

def get_cart_graph_data(request):
    filter_by = request.GET.get('filter', None)
    today_date = datetime.date.today()
    if filter_by !=None:
        if filter_by.lower()  == 'week':
            date_search =  today_date - timedelta(days=7)
            dataset = User.objects.all().filter(date_joined__gte = date_search).count()
            cart_data = ChildSchoolCart.objects.all().filter(timestamp__gte = date_search).count()
            data_title = 'Week Wise Data'
        elif filter_by.lower() == 'today':
            dataset = User.objects.all().filter(date_joined__date = today_date).count()
            cart_data = ChildSchoolCart.objects.all().filter(timestamp__date__exact = today_date).count()
            data_title = 'Today Data'
        elif filter_by.lower() == 'month':
             dataset = User.objects.all().filter(date_joined__month = today_date.month, date_joined__year = today_date.year).count()
             cart_data = ChildSchoolCart.objects.all().filter(timestamp__year = today_date.year, timestamp__month = today_date.month).count()
             data_title = 'Month Wise Data'
        else:
            dataset = User.objects.all().filter(date_joined__year = today_date.year).count()
            cart_data = ChildSchoolCart.objects.all().filter(timestamp__year = today_date.year).count()
            data_title = 'Year Wise Data'
    return JsonResponse({
            'data_title': data_title,
            'labels':['Cart Items Added','Not added in carts'],
            'count':[cart_data,dataset-cart_data]
        },safe=False)

def get_contactus_graph_data(request):
    filter_by = request.GET.get('filter', None)
    today_date = datetime.date.today()
    if filter_by !=None:
        if filter_by.lower() == 'month':
            data=ContactUs.objects.filter(created_at__year=today_date.year,created_at__month=today_date.month).annotate(month=ExtractMonth('created_at'),
                                year=ExtractYear('created_at'),day=ExtractDay('created_at'),)\
                      .values('month', 'year','day')\
                      .annotate(total=Count('*'))\
                      .values('month','year','day', 'total').order_by('created_at__year','created_at__month','created_at__day')
            list=[]

            for i in data:
                dict={}
                dict['day']= str(i['day']) +" " + str(datetime.date(i['year'], i['month'], i['day']).strftime('%B')) +" "+str(i['year'])
                dict['total']= i['total']
                list.append(dict)
            label= [i['day'] for i in list]
            count= [i['total'] for i in list]
            return JsonResponse({'labels':label,'count':count,'data_title':f'Month Wise Data For Month {today_date.month} Year {today_date.year}'})
        else:
            data=ContactUs.objects.filter(created_at__year=today_date.year).annotate(month=ExtractMonth('created_at'),
                                year=ExtractYear('created_at'),)\
                      .values('month', 'year')\
                      .annotate(total=Count('*'))\
                      .values('month','year', 'total').order_by('created_at__year','created_at__month')
            list=[]
            for i in data:
                dict={}
                dict['month']=str(datetime.date(i['year'], i['month'], 1).strftime('%B')) +" "+str(i['year'])
                dict['total']= i['total']
                list.append(dict)
            label= [i['month'] for i in list]
            count= [i['total'] for i in list]
            return JsonResponse({'labels':label,'count':count,'data_title':'Year Wise Data'})
    return JsonResponse({
            'data_title':'error'
        },safe=False)

def get_school_enquiry_graph_data(request):
    filter_by = request.GET.get('filter', None)
    today_date = datetime.date.today()
    if filter_by !=None:
        if filter_by.lower() == 'month':
            data=SchoolEnquiry.objects.filter(timestamp__year=today_date.year,timestamp__month=today_date.month).annotate(month=ExtractMonth('timestamp'),
                                year=ExtractYear('timestamp'),day=ExtractDay('timestamp'),)\
                      .values('month', 'year','day')\
                      .annotate(total=Count('*'))\
                      .values('month','year','day', 'total').order_by('timestamp__year','timestamp__month','timestamp__day')
            list=[]

            for i in data:
                dict={}
                dict['day']= str(i['day']) +" " + str(datetime.date(i['year'], i['month'], i['day']).strftime('%B')) +" "+str(i['year'])
                dict['total']= i['total']
                list.append(dict)
            label= [i['day'] for i in list]
            count= [i['total'] for i in list]
            return JsonResponse({'labels':label,'count':count,'data_title':f'Month Wise Data For Month {today_date.month} Year {today_date.year}'})
        else:
            data=SchoolEnquiry.objects.filter(timestamp__year=today_date.year).annotate(month=ExtractMonth('timestamp'),
                                year=ExtractYear('timestamp'),)\
                      .values('month', 'year')\
                      .annotate(total=Count('*'))\
                      .values('month','year', 'total').order_by('timestamp__year','timestamp__month')
            list=[]
            for i in data:
                dict={}
                dict['month']=str(datetime.date(i['year'], i['month'], 1).strftime('%B')) +" "+str(i['year'])
                dict['total']= i['total']
                list.append(dict)
            label= [i['month'] for i in list]
            count= [i['total'] for i in list]
            return JsonResponse({'labels':label,'count':count,'data_title':'Year Wise Data'})
    return JsonResponse({
            'data_title':'error'
        },safe=False)


@staff_member_required
def home(request):
    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    today_date = datetime.date.today()

    dataset = User.objects.all().filter(date_joined__year='2021').order_by('date_joined')

    query = User.objects.filter(date_joined__year = today_date.year)
    year_data = query.count()
    query = query.filter(date_joined__month = today_date.month)
    month_data = query.count()

    week_time = today_date_time - timedelta(days=7)
    week_query =  query.filter(date_joined__gte = week_time)
    week_data = week_query.count()

    query = query.filter(date_joined__range=(start_today_data,end_today_data))
    today_data = query.count()

    return render(request, 'custom_admin/dashboard.html', {
        'data':dataset,
        'today_data':today_data,
        'week_data':week_data,
        'month_data':month_data,
        'year_data':year_data
    })

@api_view(['GET'])
def pivot_data(request):
    data=User.objects.annotate(month=ExtractMonth('date_joined'),
                                year=ExtractYear('date_joined'),)\
                      .values('month', 'year')\
                      .annotate(total=Count('*'))\
                      .values('month','year', 'total').order_by('date_joined__year','date_joined__month')
    list=[]
    for i in data:
        dict={}
        dict['month']=str(datetime.date(i['year'], i['month'], 1).strftime('%B')) +" "+str(i['year'])
        dict['total']= i['total']
        list.append(dict)
    label= [i['month'] for i in list]
    count= [i['total'] for i in list]

    return Response({'labels':label,'count':count})

@api_view(['GET'])
def this_month_analytics(request):
    data=User.objects.filter(date_joined__year='2021',date_joined__month='3').annotate(month=ExtractMonth('date_joined'),
                                day=ExtractDay('date_joined'))\
                      .values('month','day')\
                      .annotate(total=Count('*'))\
                      .values('month','day','total').order_by('date_joined__day')
    list=[]
    for i in data:
        dict={}
        dict['day']=str(i['day'])+" "+str(datetime.date(2021, 3, i['day']).strftime('%B'))
        dict['total']= i['total']
        list.append(dict)
    label= [i['day'] for i in list]
    count= [i['total'] for i in list]

    return Response({'labels':label,'count':count})

@api_view(['GET'])
def get_pincodes(request):
    data = ParentAddress.objects.all()
    list=set([i.pincode for i in data])
    return Response({'pincodes':list})


@api_view(['GET'])
def get_city(request):
    data = ParentAddress.objects.all()
    list=set([i.city for i in data])
    return Response({'city':list})

@api_view(['GET'])
def get_state(request):
    data = ParentAddress.objects.all()
    list=set([i.state for i in data])
    return Response({'state':list})


@api_view(['GET'])
def get_monthly_budget(request):
    data = ParentAddress.objects.all()
    list=set([i.monthly_budget for i in data])
    return Response({'monthly_budget':list})


def get_all_child_cart_data(request):
    cursor = connection.cursor()
    filter_query = child_cart_query()
    cursor.execute(filter_query)
    data=cursor.fetchall()
    list=[]
    for i in data:
        list.append(i[11])
    tuple_data=tuple(list)
    filter_query = address_not_present_cart_query(tuple_data)
    cursor.execute(filter_query)
    data_no_address = cursor.fetchall()
    return render(request,'custom_admin/cart_items_custom.html',{
        'dataset':data,
        'no_address_dataset':data_no_address
    })

def get_all_school_enquiry(request):
    cursor = connection.cursor()
    query = school_enquiry_parent_profile_present()
    cursor.execute(query)
    data=cursor.fetchall()

    # query2 = school_enquiry_existing_parent_data()
    # cursor.execute(query2)
    # existing_parentdata=cursor.fetchall()
    # existing_parentdata=set(existing_parentdata)

    # query3 = school_enquiry_all_data()
    # alldata=cursor.execute(query3)
    # alldata=cursor.fetchall()
    # alldata=set(alldata)
    # remainingdata=alldata-existing_parentdata

    return render(request,'custom_admin/school_enquiry_custom.html',{'dataset':data,
                                                                    'no_address_dataset':''})

def get_all_contactus_data(request):
    cursor = connection.cursor()
    query ="""
            SELECT DISTINCT miscs_contactus.name,miscs_contactus.phone_number,
            miscs_contactus.message,miscs_contactus.email,
            parents_parentaddress.city,parents_parentaddress.pincode,
            parents_parentaddress.monthly_budget,
            to_char(miscs_contactus.created_at, 'DD/MM/YYYY'),accounts_user.email,
            to_char(miscs_contactus.created_at, 'YYYYMMDD')
            FROM accounts_user
            INNER JOIN miscs_contactus
            ON miscs_contactus.email=accounts_user.email
            INNER JOIN parents_parentprofile
            ON accounts_user.id = parents_parentprofile.user_id
            INNER JOIN parents_parentaddress
            ON parents_parentaddress.parent_id = parents_parentprofile.id
            ORDER BY to_char(miscs_contactus.created_at, 'YYYYMMDD') ASC
            """
    cursor.execute(query)
    data=cursor.fetchall()

    query2 = """
            SELECT DISTINCT miscs_contactus.name,miscs_contactus.phone_number,
            miscs_contactus.message,miscs_contactus.email,
            to_char(miscs_contactus.created_at, 'DD/MM/YYYY'),to_char(miscs_contactus.created_at, 'YYYYMMDD')
            FROM miscs_contactus
            ORDER BY to_char(miscs_contactus.created_at, 'YYYYMMDD')  ASC
            """
    cursor.execute(query2)
    alldata=cursor.fetchall()
    alldata=set(alldata)

    query3 ="""
            SELECT DISTINCT miscs_contactus.name,miscs_contactus.phone_number,
            miscs_contactus.message,miscs_contactus.email,to_char(miscs_contactus.created_at, 'DD/MM/YYYY')
            ,to_char(miscs_contactus.created_at, 'YYYYMMDD')
            FROM accounts_user
            INNER JOIN miscs_contactus
            ON miscs_contactus.email=accounts_user.email
            INNER JOIN parents_parentprofile
            ON accounts_user.id = parents_parentprofile.user_id
            INNER JOIN parents_parentaddress
            ON parents_parentaddress.parent_id = parents_parentprofile.id
            ORDER BY to_char(miscs_contactus.created_at, 'YYYYMMDD') ASC
             """

    cursor.execute(query3)
    prarentexist=cursor.fetchall()
    prarentexist=set(prarentexist)

    remaining=alldata-prarentexist

    return render(request,'custom_admin/contact_us.html',{'dataset':data,
                                                        'no_address_dataset':remaining})

def get_all_parent_profile_data(request):
    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    data=User.objects.all().filter(is_parent=True).prefetch_related('user_admission_forms','forms','parent_profile','user_childs','user_enquiry','child_cart_user','parent_address_user').order_by("-id")

    context = {}

    base_url = '?parent_name=&parent_email=&parent_phone=&start_date=&end_date=&enq_start_date=&enq_end_date=&'

    start_date = ''
    end_date = ''
    parent_name = ''
    parent_email = ''
    parent_phone = ''
    parent_pincode = ''
    parent_city = ''
    parent_street_address = ''
    parent_state = ''
    enq_start_date = ''
    enq_end_date = ''
    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(date_joined__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(date_joined__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
                )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'enq_start_date' in request.GET and 'enq_end_date' in request.GET and  request.GET['enq_end_date'] != '' and  request.GET['enq_start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['enq_start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['enq_end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(user_enquiry__timestamp__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(user_enquiry__timestamp__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
                ).distinct()
       # data = data.objects.district('id')
        context['enq_start_date'] = request.GET['enq_start_date']
        context['enq_end_date'] = request.GET['enq_end_date']
        enq_start_date = request.GET['enq_start_date']
        enq_end_date = request.GET['enq_end_date']

    if 'parent_name' in request.GET and  request.GET['parent_name'] != '' :
        name_search = request.GET['parent_name'].strip()
        data = data.filter(
                    name__icontains = name_search
                )
        context['name'] = name_search
        parent_name = name_search

    if 'parent_email' in request.GET and  request.GET['parent_email'] != '':
        email_search = request.GET['parent_email'].strip()
        data = data.filter(
                    email__icontains = email_search
                )
        context['email'] = email_search
        parent_email = email_search

    if 'parent_phone' in request.GET and request.GET['parent_phone'] != '':
        phone_search = request.GET['parent_phone']
        #Todo: Phone Search Remaining
        context['phone'] = phone_search
        parent_phone = phone_search


    if 'parent_pincode' in request.GET and request.GET['parent_pincode'] != '':
        pincode_search = request.GET['parent_pincode'].strip()
        data = data.filter(
            Q(user_admission_forms__pincode__icontains = pincode_search) |
            Q(parent_address_user__pincode__icontains = pincode_search)
         )
        context['parent_pincode'] = pincode_search
        parent_pincode = pincode_search

    if 'parent_state' in request.GET and request.GET['parent_state'] != '':
        state_search = request.GET['parent_state'].strip()
        data = data.filter(
            Q(user_admission_forms__state__icontains = state_search) |
            Q(parent_address_user__state__icontains = state_search)
        )
        context['parent_state'] = state_search
        parent_state = state_search

    if 'parent_street_address' in request.GET and request.GET['parent_street_address'] != '':
        street_address_search = request.GET['parent_street_address'].strip()
        data = data.filter(
            Q(user_admission_forms__street_address__icontains = street_address_search) |
            Q(parent_address_user__street_address__icontains = street_address_search) |
            Q(user_admission_forms__short_address__icontains = street_address_search)
        )
        context['parent_street_address'] = street_address_search
        parent_street_address = street_address_search

    if 'parent_city' in request.GET and request.GET['parent_city'] != '':
        city_search = request.GET['parent_city'].strip()
        data = data.filter(
            Q(parent_address_user__city__icontains = city_search) |
            Q(user_admission_forms__city__icontains = city_search)
        )
        context['parent_city'] = city_search
        parent_city = city_search



    base_url = f"?parent_name={parent_name}&parent_email={parent_email}&parent_phone={parent_phone}&start_date={start_date}&end_date={end_date}&enq_start_date={enq_start_date}&enq_end_date={enq_end_date}&parent_pincode={parent_pincode}&parent_city={parent_city}&parent_street_address={parent_street_address}&parent_state={parent_state}&"
    paginator = Paginator(data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    #print(page_obj.__dict__)
    return render(request,'custom_admin/parent_profile_custom.html',{
        'data':data,
        'page_obj': page_obj,
        'context':context,
        'base_url':base_url
    })



# def get_all_admission_guidance_data(request):
#     data = AdmissionGuidance.objects.all().order_by("-id")
#     name=""
#     email=""
#     phone_number=""
#     start_date=""
#     end_date=""
#     message=""
#     parent_state=""


#     paginator = Paginator(data, 25)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     base_url = f"?name={name}&email={email}&phone_number={phone_number}&start_date={start_date}&end_date={end_date}&message={message}&parent_state={parent_state}&"
#     return render(request,'custom_admin/Addmission_guidance_custom.html',{
#         'page_obj':page_obj,
#     })

def get_school_enquiry_for_anon_user(request):
    #data = SchoolEnquiry.objects.filter(
     #       Q( user = None )
      #  ).order_by("-id")
    data = SchoolEnquiry.objects.all().order_by("-id")
    context = {}

    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    parent_name = ''
    parent_email = ''
    parent_phone = ''
    start_date = ''
    end_date = ''
    parent_query = ''
    school_name =''
    school_region=''
    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(timestamp__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(timestamp__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'parent_name' in request.GET and request.GET['parent_name'] != '':
        parent_name = request.GET['parent_name'].strip()
        data = data.filter(
            parent_name__icontains = parent_name
        )
        context['parent_name'] = parent_name

    if 'parent_email' in request.GET and request.GET['parent_email'] != '':
        parent_email = request.GET['parent_email'].strip()
        data = data.filter(
            email__icontains = parent_email
        )
        context['parent_email'] = parent_email

    if 'parent_phone' in request.GET and request.GET['parent_phone'] != '':
        parent_phone = request.GET['parent_phone'].strip()
        data = data.filter(
            phone_no__icontains = parent_phone
        )
        context['parent_phone'] = parent_phone

    if 'parent_query' in request.GET and request.GET['parent_query'] != '':
        parent_query = request.GET['parent_query'].strip()
        data = data.filter(
            query__icontains = parent_query
        )
        context['parent_query'] = parent_query

    if 'school_name' in request.GET and request.GET['school_name'] != '':
        school_name = request.GET['school_name'].strip()
        data = data.filter(
            school__name__icontains = school_name
        )
        context['school_name'] = school_name

    if 'school_region' in request.GET and request.GET['school_region'] != '':
        school_region = request.GET['school_region'].strip()
        data = data.filter(
            school__district__name__icontains = school_region
        )
        context['school_region'] = school_region

    paginator = Paginator(data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    base_url = f"?parent_name={parent_name}&parent_email={parent_email}&parent_phone={parent_phone}&start_date={start_date}&end_date={end_date}&parent_query={parent_query}&school_name={school_name}&school_region={school_region}&"
    return render(request,'custom_admin/school_enquiry_new.html',{
        'page_obj': page_obj,
        'context':context,
        'base_url':base_url
    })



def get_contact_us_for_anon_user(request):
    data = ContactUs.objects.filter(
        user=None
    ).order_by("-id")
    context = {}

    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    name = ''
    email = ''
    phone_number = ''
    start_date = ''
    end_date = ''
    message = ''

    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(created_at__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(created_at__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'name' in request.GET and request.GET['name'] != '':
        name = request.GET['name'].strip()
        data = data.filter(
            name__icontains = name
        )
        context['name'] = name

    if 'email' in request.GET and request.GET['email'] != '':
        email = request.GET['email'].strip()
        data = data.filter(
            email__icontains = email
        )
        context['email'] = email

    if 'phone_number' in request.GET and request.GET['phone_number'] != '':
        phone_number = request.GET['phone_number'].strip()
        data = data.filter(
            phone_number__icontains = phone_number
        )
        context['phone_number'] = phone_number

    if 'message' in request.GET and request.GET['message'] != '':
        message = request.GET['message'].strip()
        data = data.filter(
            message__icontains = message
        )
        context['message'] = message

    paginator = Paginator(data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    base_url = f"?name={name}&email={email}&phone_number={phone_number}&start_date={start_date}&end_date={end_date}&message={message}&"

    return render(request,'custom_admin/contact_us_new.html',{
        'page_obj': page_obj,
        'context':context,
        'base_url':base_url
    })



def get_all_admission_guidance_data(request):
    data =  AdmissionGuidance.objects.all().order_by("-id")
    context = {}

    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    name = ''
    email = ''
    phone_number = ''
    start_date = ''
    end_date = ''
    region = ''

    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(created_at__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(created_at__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'name' in request.GET and request.GET['name'] != '':
        name = request.GET['name'].strip()
        data = data.filter(
            parent_name__icontains = name
        )
        context['name'] = name

    if 'email' in request.GET and request.GET['email'] != '':
        email = request.GET['email'].strip()
        data = data.filter(
            email__icontains = email
        )
        context['email'] = email

    if 'phone_number' in request.GET and request.GET['phone_number'] != '':
        phone_number = request.GET['phone_number'].strip()
        data = data.filter(
            phone__icontains = phone_number
        )
        context['phone_number'] = phone_number

    if 'region' in request.GET and request.GET['region'] != '':
        region = request.GET['region'].strip()
        data = data.filter(
            target_region__icontains = region
        )
        context['region'] = region

    paginator = Paginator(data, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    base_url = f"?name={name}&email={email}&phone_number={phone_number}&start_date={start_date}&end_date={end_date}&region={region}&"

    return render(request,'custom_admin/Addmission_guidance_custom.html',{
        'page_obj': page_obj,
        'context':context,
        'base_url':base_url
    })


@api_view(['GET'])
def get_cart_items(request,**kwargs):
    user_id = kwargs.get("user_id",'')
    if user_id == "":
        return Response({'error':'pass a user id'})
    cartdata = ChildSchoolCart.objects.filter(form__user__id = user_id )
    data_list = []
    for i in cartdata:
        dict_temp = {}
        dict_temp['child_name'] = i.child.name
        dict_temp['school_name'] = i.school.name
        dict_temp['timestamp'] = i.timestamp
        dict_temp['class_applying_for'] = i.child.class_applying_for.name
        data_list.append(dict_temp)
    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

@api_view(['GET'])
def get_common_registration_form_api_data(request,**kwargs):
    user_id = kwargs.get("user_id",'')
    if user_id == "":
        return Response({'error':'pass a user id'})
    parent_data = CommonRegistrationForm.objects.filter(user__id = user_id)
    data_list = []
    for i in parent_data:
        dict_temp = {}
        dict_temp['child_name'] = i.child.name
        dict_temp['dob'] = i.child.date_of_birth
        dict_temp['class_applying_for'] = i.child.class_applying_for.name
        dict_temp['address'] = {
            'short_address':i.short_address,
            'street_address':i.street_address,
            'city':i.city,
            'state':i.state,
            'pincode':i.pincode,
            'country':i.country
        }
        dict_temp['timestamp'] = i.timestamp
        data_list.append(dict_temp)
    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

@api_view(['GET'])
def get_parent_address_api_data(request,**kwargs):
    user_id = kwargs.get("user_id",'')
    if user_id == "":
        return Response({'error':'pass a user id'})
    data_list = []
    parent_data = ParentAddress.objects.filter(parent__user__id = user_id)

    if parent_data.exists():
        i = parent_data[0]
        dict_temp = {}
        dict_temp['data_coming_from'] = 'Parent Address Model'
        dict_temp['address'] = {
            'street_address':i.street_address,
            'city':i.city,
            'state':i.state,
            'pincode':i.pincode,
            'country':i.country,
        }
        dict_temp['phone_number'] = i.phone_no
        dict_temp['monthly_budget'] = i.monthly_budget
        dict_temp['timestamp'] = i.timestamp
        data_list.append(dict_temp)
    # else:
    #     common_form =  CommonRegistrationForm.objects.filter(user__id = user_id)
    #     if common_form.exists():
    #         i = common_form[0]
    #         dict_temp = {}
    #         dict_temp['data_coming_from'] = 'Form'
    #         dict_temp['address'] = {
    #                 'short_address':i.short_address,
    #                 'street_address':i.street_address,
    #                 'city':i.city,
    #                 'state':i.state,
    #                 'pincode':i.pincode,
    #                 'country':i.country,
    #         }
    #         data_list.append(dict_temp)

    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

@api_view(['GET'])
def get_parent_child_data(request,**kwargs):
    user_id = kwargs.get("user_id",'')
    if user_id == "":
        return Response({'error':'pass a user id'})
    parent_data = Child.objects.filter(user__id = user_id)
    data_list = []
    for i in parent_data:
        dict_temp = {}
        dict_temp['child_name'] = i.name
        dict_temp['dob'] = i.date_of_birth
        dict_temp['timestamp'] = i.timestamp
        dict_temp['class_applying_for'] = i.class_applying_for.name
        data_list.append(dict_temp)
    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

@api_view(['GET'])
def get_parent_profile_api_data(request,**kwargs):
    user_id = kwargs.get("user_id",'')
    if user_id == "":
        return Response({'error':'pass a user id'})
    parent_data = ParentProfile.objects.filter(user__id = user_id)
    data_list = []
    for i in parent_data:
        dict_temp = {}
        dict_temp['name'] = i.name
        dict_temp['email'] = i.email
        dict_temp['phone_number'] = i.phone
        dict_temp['gender'] = i.gender
        dict_temp['occupation'] = i.occupation
        dict_temp['address'] = {
            'street_address':i.street_address,
            'city':i.city,
            'state':i.state,
            'pincode':i.pincode,
            'country':i.country
        }
        dict_temp['office_address'] = i.office_address
        dict_temp['timestamp'] = i.timestamp
        data_list.append(dict_temp)
    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

@api_view(['GET'])
def get_school_enquiry_api(request,**kwargs):
    user_email = kwargs.get("user_email",'')
    if user_email == "":
        return Response({'error':'pass a user email'})
    cartdata = SchoolEnquiry.objects.filter(email = user_email )
    data_list = []
    for i in cartdata:
        dict_temp = {}
        dict_temp['parent_name'] = i.parent_name
        dict_temp['parent_phone_no'] = i.phone_no
        dict_temp['school_name'] = i.school.name
        dict_temp['parent_email'] = i.email
        dict_temp['query'] = i.query
        dict_temp['timestamp'] = i.timestamp
        data_list.append(dict_temp)
    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

@api_view(['GET'])
def get_school_application_api(request,**kwargs):
    user_id = kwargs.get("user_id",'')
    if user_id == "":
        return Response({'error':'pass a user id'})
    cartdata = SchoolApplication.objects.filter(user__id = user_id )
    data_list = []
    for i in cartdata:
        dict_temp = {}
        dict_temp['school_name'] = i.school.name
        dict_temp['child_name'] = i.child.name
        dict_temp['class_applying_for'] = i.child.class_applying_for.name
        dict_temp['timestamp'] = i.timestamp
        data_list.append(dict_temp)
    if len(data_list) == 0:
        return Response({'no_data':0})
    return Response({'data':data_list})

def get_all_school_application_data(request):
    return render(request,'custom_admin/school_application_custom.html')




def get_all_cart_enquiry(request):
    cursor = connection.cursor()
    query="""SELECT DISTINCT schools_schoolenquiry.parent_name,schools_schoolenquiry.phone_no,
            array_to_string(array_agg(schools_schoolenquiry.query,schools_schoolprofile.name)) as Group1,
            schools_schoolenquiry.email
            From accounts_user
            FULL OUTER JOIN schools_schoolenquiry ON
            schools_schoolenquiry.email = accounts_user.email
            INNER JOIN schools_schoolprofile ON
            schools_schoolenquiry.school_id=schools_schoolprofile.id
            """

    cursor.execute(query)
    prarentexist=cursor.fetchall()
    print(len(prarentexist))
    return render(request,'custom_admin/parent_profile_custom.html',{"dataset":prarentexist})
class ParentTableView(SingleTableMixin, FilterView):
    model = ParentProfile
    table_class = ParentTable
    template_name = 'custom_admin/parent_custom.html'
    filterset_class = ParentFilter

    def get_queryset(self, **kwargs):
        users = User.objects.filter(
            is_parent=True).only(
            "id",
            "is_parent").values_list(
            "current_parent",
            flat=True)
        return ParentProfile.objects.select_related("user").annotate(
            child_count=Count("user__user_childs")).filter(pk__in=users)


class SchoolViewTableView(ExportMixin, SingleTableMixin, FilterView):
    model = SchoolView
    table_class = SchoolViewTable
    template_name = 'custom_admin/school_view_custom.html'
    filterset_class = SchoolViewFilter

    def get_queryset(self, **kwargs):
        return SchoolView.objects.all().select_related("school", "user")




# class ChildSchoolCartTableView(ExportMixin, SingleTableMixin):
#     # model = ChildSchoolCart
#     # table_class = ChildSchoolCartTable
#     template_name = 'custom_admin/cart_items_custom.html'
#     # filterset_class = ChildSchoolCartFilter

#     def get_queryset(self, **kwargs):
#         if self.request.GET.get('search'):
#             search = self.request.GET['search']
#             return ChildSchoolCart.objects.filter(Q(child__name__icontains = search) | Q(school__name__icontains = search) | Q(form__father__name = search)| Q(form__guardian__name = search)| Q(form__mother__name = search)).select_related(
#             "school", "child", "form__user", "child__class_applying_for")
#         return ChildSchoolCart.objects.all().select_related(
#             "school", "child", "form__user", "child__class_applying_for")


class SchoolApplicationTableView(ExportMixin, SingleTableMixin, FilterView):
    model = SchoolApplication
    table_class = SchoolApplicationTable
    template_name = 'custom_admin/school_applications_custom.html'
    filterset_class = SchoolApplicationFilter

    def get_queryset(self, **kwargs):
        return SchoolApplication.objects.all().select_related(
            "school", "child", "user", "apply_for", "school__region")






# class SchoolEnquiryTableView(ExportMixin, SingleTableMixin, FilterView):
#     model = SchoolEnquiry
#     table_class = SchoolEnquiryTable
#     template_name = 'custom_admin/school_enquiry_custom.html'
#     filterset_class = SchoolEnquiryFilter

#     def get_queryset(self, **kwargs):
#         return SchoolEnquiry.objects.select_related("user", "school").all()


@staff_member_required
def form_details(request, pk=None):
    parent_form = get_object_or_404(CommonRegistrationForm, pk=pk)
    context = {
        "parent_form": parent_form,
    }
    return render(request, "custom_admin/form_details.html", context)


class SchoolAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SchoolProfile.objects.none()
        qs = SchoolProfile.objects.order_by("name")
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs


class RegionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Region.objects.none()
        qs = Region.objects.order_by("name")
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs





class SchoolDetailView(DetailView):
    model = SchoolProfile
    pk_url_kwarg = 'id'
    template_name = 'custom_admin/school-details.html'


@csrf_exempt
@decorators.login_required(login_url='/custom-admin/uniform-app/login')
def uniform_app_analysis(request, template_name='custom_admin/analysis.html'):

   cursor = connection.cursor()

   filter="""
   SELECT DISTINCT accounts_user.id,parents_parentprofile.name,parents_parentprofile.parent_type,parents_parentprofile.email,
   childs_child.name,parents_parentprofile.phone,schools_schoolprofile.name,
   schools_schoolclasses.name,admission_forms_formreceipt.form_fee,schools_schoolprofile.convenience_fee,
   admission_forms_formreceipt.receipt_id,admission_forms_commonregistrationformafterpayment.session ,admission_forms_schoolapplication.timestamp
   FROM admission_forms_schoolapplication
   INNER JOIN admission_forms_commonregistrationformafterpayment
   ON admission_forms_schoolapplication.registration_data_id = admission_forms_commonregistrationformafterpayment.id
   INNER JOIN parents_parentprofile
   ON admission_forms_schoolapplication.user_id = parents_parentprofile.user_id
   INNER JOIN schools_schoolclasses
   ON schools_schoolclasses.id = admission_forms_schoolapplication.apply_for_id
   INNER JOIN childs_child
   ON admission_forms_schoolapplication.child_id = childs_child.id
   INNER JOIN schools_schoolprofile
   ON admission_forms_schoolapplication.school_id = schools_schoolprofile.id
   INNER JOIN admission_forms_formreceipt
   ON admission_forms_schoolapplication.uid = admission_forms_formreceipt.receipt_id
   INNER JOIN accounts_user
   ON accounts_user.id=admission_forms_schoolapplication.user_id  WHERE  accounts_user.is_uniform_app = {is_uniform_app}
   AND (parents_parentprofile.parent_type{parent_type} );
   """


   uniform_app_user=ParentProfile.objects.filter(user__is_uniform_app=True)
   parent_type="='father'"
   if request.method =='POST':
       if request.POST.get('parent') :
           parent_type="='{p}'".format(p=request.POST.get('parent'))
           if(parent_type=="='All'"):
               parent_type="!='null'"

   cursor.execute(filter.format(is_uniform_app=True,
                                    parent_type=parent_type
                                    ))
   userdata=cursor.fetchall()


   context_dict = {'listings': userdata,'uniform_app_user':uniform_app_user}
   return render(request, template_name, context_dict)


@csrf_exempt
def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(request, username=username, password=password)
        if user != None :
            login(request, user)
            return redirect("/custom-admin/uniform-app/")
        else:
            messages.error(request, 'Invalid credentials!!',extra_tags='alert-danger')
            return redirect("/custom-admin/uniform-app/login/")
    return render(request, "custom_admin/uniform-app-login.html", {"form": form})

@csrf_exempt
def logout_view(request):
    logout(request)
    return render(request,"custom_admin/uniform-app-logout.html",{})


def get_father_name(data):
    if(data.exists()):
        for i in data:
            form={}
            if(i.father):
               return i.father.name
            return ""
    else:
        return ""

def get_father_email(data):
    if(data.exists()):
        for i in data:
            if(i.father):
               return i.father.email
            return ""
    else:
        return ""


def get_father_phone(data):
    if(data.exists()):
        for i in data:
            if(i.father):
               return i.father.phone
            return ""
    else:
        return ""


def get_mother_name(data):
    if(data.exists()):
        for i in data:
            form={}
            if(i.mother):
               return i.mother.name
            return ""
    else:
        return ""

def get_mother_email(data):
    if(data.exists()):
        for i in data:
            if(i.mother):
               return i.mother.email
            return ""
    else:
        return ""


def get_mother_phone(data):
    if(data.exists()):
        for i in data:
            if(i.mother):
               return i.mother.phone
            return ""
    else:
        return ""

def get_guardian_name(data):
    if(data.exists()):
        for i in data:
            form={}
            if(i.guardian):
               return i.guardian.name
            return ""
    else:
        return ""

def get_guardian_email(data):
    if(data.exists()):
        for i in data:
            if(i.guardian):
               return i.guardian.email
            return ""
    else:
        return ""


def get_guardian_phone(data):
    if(data.exists()):
        for i in data:
            if(i.guardian):
               return i.guardian.phone
            return ""
    else:
        return ""


def get_applied_schools(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['child']=i.child.name
            form['Uid']=i.uid
            form['school_applied']=i.school.name
            form['applied_for']=i.apply_for.name
            list.append(form)
        return list
    else:
        return ""

def get_enquiry(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['query']=i.query
            form['phone']=i.phone_no
            form['email']=i.email
            form['school_applied']=i.school.name
            list.append(form)
        return list
    else:
        return ""


def get_common_form(data):
    if(data.exists()):
        list=[]
        for i in data:
            if((i.short_address != None) and (i.street_address != None) and (i.city != None) and (i.pincode != None) and (i.state !=None)):
                address=i.short_address+" "+i.street_address+" "+i.city+" "+str(i.pincode)+" "+i.state
                if address not in list:
                    list.append(address)
        return '  ||'.join(list)
    else:
        return ""


def get_user_childs(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['name']=i.name
            if(i.class_applying_for):
                form['class_applying_for']=i.class_applying_for.name
            else:
                form['class_applying_for']='N/A'
            form['age']=i.age_str
            if form not in list:
                list.append(form)
        return list
    else:
        return ""

def get_phoneno(data):
    if(data.exists()):
        phone_list=[]
        for i in data:
            if(i.phone != None):
                if(i.phone not in phone_list):
                    phone_list.append(i.phone)
            else:
                pass
        return ','.join(map(str, phone_list))
    else:
        return ""


def get_cart_details(data):
    if (data.exists()):
        cart_list=[]
        for i in data:
            string = """
                     {username} have added {schoolname} in cart applying for {child_name} and for {applying_for}
                     """
            string = string.format(username=i.user.first_name,
                                schoolname=i.school.name,
                                child_name=i.child.name,
                                applying_for=i.child.class_applying_for.name)
            cart_list.append(string)
        return ','.join(cart_list)
    else:
        return ""

def get_street_address(data):
    if(data.exists()):
        return data[0].street_address
    else:
        return ""

def get_parent_city(data):
    if(data.exists()):
        return data[0].city
    else:
        return ""

def get_parent_state(data):
    if(data.exists()):
        return data[0].state
    else:
        return ""

def get_parent_mothly_budget(data):
    if(data.exists()):
        return data[0].monthly_budget
    else:
        return ""


def get_parent_pincode(data):
    if(data.exists()):
        return data[0].pincode
    else:
        return ""

def get_parent_country(data):
    if(data.exists()):
        return data[0].country
    else:
        return ""


@api_view(['GET'])
def Export(request,**kwargs):
    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    data=User.objects.all().filter(is_parent=True).prefetch_related('user_admission_forms','forms','parent_profile','user_childs','user_enquiry','child_cart_user','parent_address_user').order_by("-id")

    context = {}

    base_url = '?parent_name=&parent_email=&parent_phone=&start_date=&end_date=&'

    start_date = ''
    end_date = ''
    parent_name = ''
    parent_email = ''
    parent_phone = ''
    parent_pincode = ''
    parent_city = ''
    parent_street_address = ''
    parent_state = ''

    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(date_joined__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(date_joined__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'parent_name' in request.GET and  request.GET['parent_name'] != '' :
        name_search = request.GET['parent_name']
        data = data.filter(
                    name__icontains = name_search
                )
        context['name'] = name_search
        parent_name = name_search

    if 'parent_email' in request.GET and  request.GET['parent_email'] != '':
        email_search = request.GET['parent_email']
        data = data.filter(
                    email__icontains = email_search
                )
        context['email'] = email_search
        parent_email = email_search

    if 'parent_phone' in request.GET and request.GET['parent_phone'] != '':
        phone_search = request.GET['parent_phone']
        #Todo: Phone Search Remaining
        context['phone'] = phone_search
        parent_phone = phone_search

    if 'parent_pincode' in request.GET and request.GET['parent_pincode'] != '':
        pincode_search = request.GET['parent_pincode'].strip()
        data = data.filter(
            Q(user_admission_forms__pincode__icontains = pincode_search) |
            Q(parent_address_user__pincode__icontains = pincode_search)
         )
        context['parent_pincode'] = pincode_search
        parent_pincode = pincode_search

    if 'parent_state' in request.GET and request.GET['parent_state'] != '':
        state_search = request.GET['parent_state'].strip()
        data = data.filter(
            Q(user_admission_forms__state__icontains = state_search) |
            Q(parent_address_user__state__icontains = state_search)
        )
        context['parent_state'] = state_search
        parent_state = state_search

    if 'parent_street_address' in request.GET and request.GET['parent_street_address'] != '':
        street_address_search = request.GET['parent_street_address'].strip()
        data = data.filter(
            Q(user_admission_forms__street_address__icontains = street_address_search) |
            Q(parent_address_user__street_address__icontains = street_address_search) |
            Q(user_admission_forms__short_address__icontains = street_address_search)
        )
        context['parent_street_address'] = street_address_search
        parent_street_address = street_address_search

    if 'parent_city' in request.GET and request.GET['parent_city'] != '':
        city_search = request.GET['parent_city'].strip()
        data = data.filter(
            Q(parent_address_user__city__icontains = city_search) |
            Q(user_admission_forms__city__icontains = city_search)
        )
        context['parent_city'] = city_search
        parent_city = city_search


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Bulk.csv"'
    writer = csv.DictWriter(
        response,
        fieldnames=[
            'Date Join',
            'User',
            'Email',
            'Phone',
            'Street Address',
            'City',
            'State',
            'Pincode',
            'Country',
            'Monthly Budget',
            'Father Name',
            'Father Email',
            'Father Phone',
            'Mother Name',
            'Mother Email',
            'Mother Phone',
            'Guardian Name',
            'Guardian Email',
            'Guardian Phone',
            'Applied School list',
            'Address List',
            'Childs List',
            'Enquiry List',
            'Cart Items Details'
        ]
    )
    writer.writeheader()
    for i in data:
        writer.writerow({
        'Date Join':i.date_joined.strftime("%d-%m-%Y"),
        'User':i.name,
        'Email':i.email,
        'Phone':get_phoneno(i.parent_profile.all()),
        'Street Address':get_street_address(i.parent_address_user.all()),
        'City': get_parent_city(i.parent_address_user.all()),
        'State':get_parent_state(i.parent_address_user.all()),
        'Pincode':get_parent_pincode(i.parent_address_user.all()),
        'Country':get_parent_country(i.parent_address_user.all()),
        'Monthly Budget':get_parent_mothly_budget(i.parent_address_user.all()),
        'Father Name':get_father_name(i.user_admission_forms.all()),
        'Father Email':get_father_email(i.user_admission_forms.all()),
        'Father Phone':get_father_phone(i.user_admission_forms.all()),
        'Mother Name':get_mother_name(i.user_admission_forms.all()),
        'Mother Email':get_mother_email(i.user_admission_forms.all()),
        'Mother Phone':get_mother_phone(i.user_admission_forms.all()),
        'Guardian Name':get_guardian_name(i.user_admission_forms.all()),
        'Guardian Email':get_guardian_email(i.user_admission_forms.all()),
        'Guardian Phone':get_guardian_phone(i.user_admission_forms.all()),
        'Applied School list':get_applied_schools(i.forms.all()),
        'Address List':get_common_form(i.user_admission_forms.all()),
        'Childs List':get_user_childs(i.user_childs.all()),
        'Enquiry List':get_enquiry(i.user_enquiry.all()),
        'Cart Items Details': get_cart_details(i.child_cart_user.all())
        })
    return response


@api_view(['GET'])
def export_get_school_enquiry_for_anon_user(request,**kwargs):
    data = SchoolEnquiry.objects.filter(
            Q( user = None )
        ).order_by("-id")
    context = {}

    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    parent_name = ''
    parent_email = ''
    parent_phone = ''
    start_date = ''
    end_date = ''
    parent_query = ''
    school_name =''
    school_region=''
    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(timestamp__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(timestamp__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'parent_name' in request.GET and request.GET['parent_name'] != '':
        parent_name = request.GET['parent_name'].strip()
        data = data.filter(
            parent_name__icontains = parent_name
        )
        context['parent_name'] = parent_name

    if 'parent_email' in request.GET and request.GET['parent_email'] != '':
        parent_email = request.GET['parent_email'].strip()
        data = data.filter(
            email__icontains = parent_email
        )
        context['parent_email'] = parent_email

    if 'parent_phone' in request.GET and request.GET['parent_phone'] != '':
        parent_phone = request.GET['parent_phone'].strip()
        data = data.filter(
            phone_no__icontains = parent_phone
        )
        context['parent_phone'] = parent_phone

    if 'parent_query' in request.GET and request.GET['parent_query'] != '':
        parent_query = request.GET['parent_query'].strip()
        data = data.filter(
            query__icontains = parent_query
        )
        context['parent_query'] = parent_query

    if 'school_name' in request.GET and request.GET['school_name'] != '':
        school_name = request.GET['school_name'].strip()
        data = data.filter(
            school__name__icontains = school_name
        )
        context['school_name'] = school_name

    if 'school_region' in request.GET and request.GET['school_region'] != '':
        school_region = request.GET['school_region'].strip()
        data = data.filter(
            school__region__name__icontains = school_region
        )
        context['school_region'] = school_region


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    writer = csv.DictWriter(
        response,
        fieldnames=[
            'Date of Query',
            'Parent Name',
            'Parent Email',
            'Parent Phone',
            'School Name',
            'School Region',
            'Parent Query'
        ]
    )
    writer.writeheader()
    for i in data:
        if i.timestamp:
            time = i.timestamp
        else:
            time = ''
        if i.email:
            email = i.email
        else:
            email = ''
        if i.parent_name:
            parent_name = i.parent_name
        else:
            parent_name = ''
        if i.phone_no:
            phone_no = i.phone_no
        else:
            phone_no = ''
        if i.school:
            school_name = i.school.name
            if i.school.region:
                region_name = i.school.region.name
            else:
                region_name = ''
        else:
            region_name = ''
            school_name = ''

        if i.query:
            query = i.query
        else:
            query = ''
        writer.writerow({
        'Date of Query':time,
        'Parent Name':parent_name,
        'Parent Email':email,
        'Parent Phone':phone_no,
        'School Name':school_name,
        'School Region':region_name,
        'Parent Query':query
        })
    return response


@api_view(['GET'])
def export_get_contact_us_for_anon_user(request,**kwargs):
    data = ContactUs.objects.filter(
        user=None
    ).order_by("-id")
    context = {}

    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    name = ''
    email = ''
    phone_number = ''
    start_date = ''
    end_date = ''
    message = ''

    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(created_at__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(created_at__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'name' in request.GET and request.GET['name'] != '':
        name = request.GET['name'].strip()
        data = data.filter(
            name__icontains = name
        )
        context['name'] = name

    if 'email' in request.GET and request.GET['email'] != '':
        email = request.GET['email'].strip()
        data = data.filter(
            email__icontains = email
        )
        context['email'] = email

    if 'phone_number' in request.GET and request.GET['phone_number'] != '':
        phone_number = request.GET['phone_number'].strip()
        data = data.filter(
            phone_number__icontains = phone_number
        )
        context['phone_number'] = phone_number

    if 'message' in request.GET and request.GET['message'] != '':
        message = request.GET['message'].strip()
        data = data.filter(
            message__icontains = message
        )
        context['message'] = message


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    writer = csv.DictWriter(
        response,
        fieldnames=[
            'Date of Message',
            'Name',
            'Email',
            'Phone',
            'Message'
        ]
    )
    writer.writeheader()
    for i in data:
        writer.writerow({
            'Date of Message':i.created_at,
            'Name':i.name,
            'Email':i.email,
            'Phone':i.phone_number,
            'Message':i.message
        })
    return response




@api_view(['GET'])
def export_csv_admission_guidance(request,**kwargs):
    data =  AdmissionGuidance.objects.all().order_by("-id")
    context = {}

    today_date_time = localtime()
    start_today_data = today_date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_today_data = today_date_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    name = ''
    email = ''
    phone_number = ''
    start_date = ''
    end_date = ''
    region = ''

    if 'start_date' in request.GET and 'end_date' in request.GET and  request.GET['end_date'] != '' and  request.GET['start_date'] != '':
        date_search = datetime_custom.strptime(request.GET['start_date'],'%Y-%m-%dT%H:%M')
        date_search_end = datetime_custom.strptime(request.GET['end_date'],'%Y-%m-%dT%H:%M')
        data = data.filter(
                Q(created_at__gte = today_date_time.replace(date_search.year,date_search.month,date_search.day,date_search.hour,date_search.minute,0,0))
                &
                Q(created_at__lte = today_date_time.replace(date_search_end.year,date_search_end.month,date_search_end.day,date_search_end.hour,date_search_end.minute,59,99999))
        )
        context['start_date'] = request.GET['start_date']
        context['end_date'] = request.GET['end_date']
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

    if 'name' in request.GET and request.GET['name'] != '':
        name = request.GET['name'].strip()
        data = data.filter(
            parent_name__icontains = name
        )
        context['name'] = name

    if 'email' in request.GET and request.GET['email'] != '':
        email = request.GET['email'].strip()
        data = data.filter(
            email__icontains = email
        )
        context['email'] = email

    if 'phone_number' in request.GET and request.GET['phone_number'] != '':
        phone_number = request.GET['phone_number'].strip()
        data = data.filter(
            phone__icontains = phone_number
        )
        context['phone_number'] = phone_number

    if 'region' in request.GET and request.GET['region'] != '':
        region = request.GET['region'].strip()
        data = data.filter(
            target_region__icontains = region
        )
        context['region'] = region

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    writer = csv.DictWriter(
        response,
        fieldnames=[
            'Date Registered',
            'Name',
            'Email',
            'Phone',
            'Message',
            'Target Region'
        ]
    )
    writer.writeheader()
    for i in data:
        writer.writerow({
            'Date Registered':i.created_at,
            'Name':i.parent_name,
            'Email':i.email,
            'Phone':i.phone,
            'Message':i.message,
            'Target Region':i.target_region

        })

    return response
