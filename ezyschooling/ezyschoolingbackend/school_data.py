import random

import requests
from django.core.files.base import ContentFile
from django.db.models import Max
from faker import Faker

from schools.models import (
                SchoolClasses,
                SchoolType,
                Board,
                Region,
                State,
                SchoolProfile,
                Gallery,
                DistancePoint,
                AdmmissionOpenClasses,
                FeeStructure,
                ActivityType,
                ActivityImageSlider,
                Activity,
                ContactModel,
                SchoolView,
            )

fake = Faker()


for i in range(10):
    Region.objects.create(name=fake.name(), rank=random.randint(1,20), active=True)


for i in range(10):
    State.objects.create(name=fake.name(), rank=random.randint(1,20), active=True)


for i in range(10):
    Board.objects.create(name=fake.name())


for i in range(10):
    SchoolType.objects.create(name=fake.name())


for i in range(10):
    SchoolClasses.objects.create(name=fake.name(), rank=random.randint(1,10))


max_schoolclasses_id = SchoolClasses.objects.last().id

def random_schoolclasses():
    pk = random.randint(1, max_schoolclasses_id)
    try:
        return SchoolClasses.objects.get(pk=pk)
    except:
        return random_schoolclasses()


max_region_id = Region.objects.last().id

def random_region():
    pk = random.randint(1, max_region_id)
    try:
        return Region.objects.get(pk=pk)
    except:
        return random_region()


max_school_type_id = SchoolType.objects.last().id

def random_school_type():
    pk = random.randint(1, max_school_type_id)
    try:
        return SchoolType.objects.get(pk=pk)
    except:
        return random_school_type()


max_school_board_id = Board.objects.last().id

def random_school_board():
    pk = random.randint(1, max_school_board_id)
    try:
        return Board.objects.get(pk=pk)
    except:
        return random_school_board()


max_city_id = Region.objects.last().id

def random_city():
    pk = random.randint(1, max_city_id)
    try:
        return Region.objects.get(pk=pk)
    except:
        return random_city()


max_state_id = State.objects.last().id

def random_state():
    pk = random.randint(1, max_state_id)
    try:
        return State.objects.get(pk=pk)
    except:
        return random_state()


for i in range(200):
    email = fake.email()
    username = email.split("@")[0]
    name = fake.name()
    user = User.objects.create(username=username, email=email, password="shekhar@123")
    school = SchoolProfile.objects.create(user=user,
            name=fake.text()[:50],
            email=email,
            phone_no="999999999",
            website="http://shekharnunia.com",
            school_timings=fake.name(),
            school_type=random_school_type(),
            school_board=random_school_board(),
            region=random_region(),
            state=random_state(),
            longitude=77.2915000000000000,
            latitude=28.6225000000000000,
            school_category="Boys",
        )
    for i in range(random.randint(1, 10)):
        school.class_relation.add(random_schoolclasses())
    for class_ in school.class_relation.all():
        FeeStructure.objects.create(class_relation=class_, school=school, active=random.randint(0, 1), fee_price=random.randint(100,1000), draft=random.randint(0, 1))
        AdmmissionOpenClasses.objects.create(class_relation=class_, school=school, admission_open=random.randint(0, 1), form_limit=random.randint(100,1000), draft=random.randint(0, 1), available_seats=random.randint(0, 1))

