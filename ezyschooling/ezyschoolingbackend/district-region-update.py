import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

# from schools.models import DistrictRegion

# all_region = DistrictRegion.objects.all().order_by("city")

# for region in all_region:
#     if region.latitude and region.longitude:
#         pass
#     else:
#         region.save()
#         print(f"{region.name}, {region.city.name} -> Updated")
from accounts.models import User
from admission_forms.models import ChildSchoolCart, SchoolApplication
from datetime import date, timedelta
from schools.models import SchoolEnquiry, Region,SchoolProfile,City,AdmissionSession,AdmmissionOpenClasses
from discussions.models import Discussion
from parents.models import ParentProfile,ParentAddress

def user_no_activity_mail_30_day():
    from_date = date.today() - timedelta(days=20)
    to_date = date.today() - timedelta(days=11)
    print(from_date,to_date)
    # users = User.objects.all().filter(is_parent=True, last_login__date__range=(from_date, to_date)).order_by("-id")
    users = User.objects.all().filter(is_parent=True, date_joined__date__range=(from_date, to_date)).order_by("id")

    for item in users:
        # try:
        if not ChildSchoolCart.objects.filter(user__id=item.id).exists() and not SchoolEnquiry.objects.filter(user__parent_profile=item.id).exists() and not SchoolApplication.objects.filter(user__id=item.id).exists():
            if not item.current_parent == -1:
                parent = ParentProfile.objects.get(id=item.current_parent)
                username = parent.name or item.name or 'Parent'
                email = item.email or parent.email
                phone = ''
                school_list = []
                count = 0
                parentaddress = ParentAddress.objects.filter(parent=parent).first()
                if parentaddress and parentaddress.region:
                    print('hello')
                    region = Region.objects.filter(name=parentaddress.region).first()
                    city= City.objects.filter(name=region.name).first()
                    school = SchoolProfile.objects.filter(school_city=city.id,collab=True)
                    for i in school:
                        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                        if AdmmissionOpenClasses.objects.filter(school__id=i.id,admission_open= "OPEN", session=currentSession).exists() or AdmmissionOpenClasses.objects.filter(school__id=i.id,admission_open= "OPEN", session=currentSession).exists():
                            count += 1
                            school_list.append(
                                {
                                'name': i.name,
                                'logo': i.logo.url,
                                'slug': i.slug,
                                'address': f"{i.district_region.name, i.district.name}"
                            })
                            if count > 8:
                                break
                else:
                    print("helli")
                    city_ids =[1,5,9,15]
                    for id in city_ids:
                        schoolList = SchoolProfile.objects.filter(school_city__id=id,collab=True)[:2]
                        for school in schoolList:
                            school_list.append({
                                'name': school.name,
                                'logo': school.logo.url,
                                'slug': school.slug,
                                'address': f"{school.district_region.name, school.district.name}"
                            })

                print(school_list)
                
        # except:
        #     pass

user_no_activity_mail_30_day()