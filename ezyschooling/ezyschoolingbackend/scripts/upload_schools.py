import csv
import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()


from schools.models import *
from io import BytesIO
from django.core.files import File
import requests

FACILITIES_DATA = {
    "Sports": [
        "Gym",
        "Indoor Sports",
        "Outdoor Sports",
        "Swimming Pool",
        "Karate",
        "Taekwondo",
        "Yoga"
    ],

    "Labs": [
        "Computer Lab",
        "Science Lab",
        "Robotics Lab"
    ],

    "Safety & Security": [
        "CCTV",
        "GPS Bus Tracking App",
        "Student Tracking App"
    ],

    "Extra Curricular": [
        "Art and Craft",
        "Dance",
        "Debate",
        "Drama",
        "Gardening",
        "Music",
        "Picnics and excursion"
    ],

    "Infrastructure": [
        "Auditorium/Media Room",
        "Cafeteria/Canteen",
        "Library/Reading Room",
        "Playground"
    ],

    "Boarding": [
        "Boys Hostel",
        "Girls Hostel"
    ],

    "Class": [
        "AC Classes",
        "Smart Classes",
        "Wifi"
    ],

    "Advanced Facilities": [
        "Alumni Association",
        "Day care",
        "Medical Room",
        "Transportation",
        "Meals"
    ],

    "Disabled Friendly": [
        "Ramps",
        "Washrooms",
        "Elevators"
    ]
}

with open('School_Data_Uploading.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            pass
        line_count += 1

        #print(row["\ufeffschool_name"])
        print(row["school_name"])

        school = SchoolProfile.objects.create(
            user_id=38741,
            name=row["school_name"],
            #name=row["\ufeffschool_name"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            academic_session=row["academic_session"],
            short_address=row["address_line1"],
            street_address=row["address_line2"],
            city=row["city"],
            #state_id=int(row["state"]),
            zipcode=row["pincode"],
            description=f"Consists of classes {row['classes_offered']}",
            year_established=row["year_established"],
            #ownership=row["ownership"],
            ownership="P",
            student_teacher_ratio=row["student_teacher_ratio"],
            website=row["website"],
            email=row["email"],
            phone_no=row["phone_no"],
            is_active=True,
            is_verified=True,
        )

        if row["region"] not in [None, ""]:
            school.region_id = 3
            #school.region_id = int(row["region"])

        if row["state"] not in ["", None]:
            school.state_id = 1
            #school.state_id = int(row["state"])
        
        if row["board"] not in [None, '']:
            school.school_board_id = 1
            #school.school_board_id = int(row["board"])

        if row["school_format"] not in [None, '']:
            school.school_format_id = 1
            #school.school_format_id = int(row["school_format"])

        if row["school_category"]:
            school.school_category = row["school_category"]

        school.save()
        logo = requests.get(row["logo"])
        logo_name = logo.url.split("/")[-1]
        logo_content = logo.content

        school.logo.save(logo_name, BytesIO(logo_content))

        classes = {
            "Pre-Nursery": 11,
            "Nursery": 12,
            "Class 1": 1,
            "Class 2": 2,
            "Class 3": 3,
            "Class 4": 4,
            "Class 5": 5,
            "Class 6": 6,
            "Class 7": 7,
            "Class 8": 8,
            "Class 9": 9,
            "Class 10": 10,
            "Class 11": 14,
            "Class 12": 15,
            "KG": 13
        }

        for _class in classes.keys():
            if row[_class]:
                FeeStructure.objects.create(class_relation_id=classes[_class], school=school, fee_price=row[_class])

        if row["facilities"]:
            facilities = eval(row["facilities"])

            for fac in facilities:
                print(fac)
                fac_type = [k for k, v in FACILITIES_DATA.items() if fac in v][0]
                act_type, _ = ActivityType.objects.get_or_create(
                    school=school,
                    name=fac_type,
                )
                Activity.objects.create(
                    activity_type = act_type,
                    name=fac,
                )

        if row["gallery"]:
            gallery = eval(row["gallery"])
            for gal in gallery:
                g = Gallery.objects.create(school=school)
                _gal = requests.get(gal)
                gal_name = _gal.url.split("/")[-1]
                gal_content = _gal.content
                gal_file = BytesIO(gal_content)
                g.image.save(gal_name, File(gal_file))

