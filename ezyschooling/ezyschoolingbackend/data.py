import random

import requests
from django.core.files.base import ContentFile
from django.db.models import Max
from faker import Faker

from accounts.models import User
from articles.models import ExpertArticle, ExpertArticleComment
from categories.models import Board, ExpertUserVideoCategory, SubCategory
from discussions.models import Discussion, DiscussionComment
from experts.models import ExpertUserProfile
from news.models import News, NewsHeadline
from parents.models import ParentProfile
from tags.models import CustomTag, Tagged
from videos.models import ExpertUserVideo, ExpertVideoComment

fake = Faker()




for i in range(100):
    CustomTag.objects.get_or_create(name=fake.name())


max_tag_id = CustomTag.objects.all().aggregate(max_tag_id=Max("id"))["max_tag_id"]


def random_tag():
    pk = random.randint(1, max_tag_id)
    try:
        return CustomTag.objects.get(pk=pk)
    except:
        return random_tag()


for tag in CustomTag.objects.all():
    for i in range(random.randint(1, 20)):
        tag.similar_tag.add(random_tag())


for i in range(20):
    email = fake.email()
    username = email.split("@")[0]
    user = User.objects.create(username=username, email=email, password="shekhar123")
    ExpertUserProfile.objects.create(
        user=user, name=fake.name(), is_expert_panel=random.randint(0, 1),
    )

for i in range(20):
    email = fake.email()
    username = email.split("@")[0]
    name = fake.name()
    user = User.objects.create(username=username, email=email, password="shekhar123")
    gender = ["male", "female"]
    parent_type = ["father", "mother"]
    ParentProfile.objects.create(
        user=user,
        gender=random.choice(gender),
        name=name,
        email=email,
        parent_type=random.choice(parent_type),
    )


max_board_id = Board.objects.all().aggregate(max_board_id=Max("id"))["max_board_id"]


def random_board():
    pk = random.randint(1, max_board_id)
    try:
        return Board.objects.get(pk=pk)
    except:
        return random_board()


max_sub_category_id = SubCategory.objects.all().aggregate(
    max_sub_category_id=Max("id")
)["max_sub_category_id"]


def random_sub_category():
    pk = random.randint(1, max_sub_category_id)
    try:
        return SubCategory.objects.get(pk=pk)
    except:
        return random_sub_category()


max_category_id = ExpertUserVideoCategory.objects.all().aggregate(
    max_category_id=Max("id")
)["max_category_id"]


def random_category():
    pk = random.randint(1, max_category_id)
    try:
        return ExpertUserVideoCategory.objects.get(pk=pk)
    except:
        return random_category()


max_expert_id = ExpertUserProfile.objects.all().aggregate(max_expert_id=Max("id"))[
    "max_expert_id"
]


def random_expert():
    pk = random.randint(1, max_expert_id)
    try:
        return ExpertUserProfile.objects.get(pk=pk)
    except:
        return random_expert()


max_parent_id = ParentProfile.objects.all().aggregate(max_parent_id=Max("id"))[
    "max_parent_id"
]


def random_parent():
    pk = random.randint(1, max_parent_id)
    try:
        return ParentProfile.objects.get(pk=pk)
    except:
        return random_parent()


max_user_id = User.objects.all().aggregate(max_user_id=Max("id"))["max_user_id"]


def random_user():
    pk = random.randint(1, max_user_id)
    try:
        return User.objects.get(pk=pk)
    except:
        return random_user()


for i in range(500):
    title = fake.paragraph()
    description = (
        fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
    )
    article = ExpertArticle.objects.create(
        title=title,
        board=random_board(),
        sub_category=random_sub_category(),
        created_by=random_expert(),
        description=description,
        views=random.randint(1, 100),
        status="P",
    )

    img_url = "https://loremflickr.com/720/640"
    name = article.title[:100]
    response = requests.get(img_url)

    if response.status_code == 200:
        article.thumbnail.save(name, ContentFile(response.content), save=True)

    for i in range(random.randint(1, 10)):
        article.likes.add(random_user())
    for i in range(random.randint(1, 10)):
        article.tags.add(random_tag())


for i in range(500):
    title = fake.paragraph()
    urls = [
        "https://www.youtube.com/watch?v=IerYs2XMXmw",
        "https://www.youtube.com/watch?v=afxb39mgg34",
        "https://www.youtube.com/watch?v=bU5cNViP2N0",
        "https://www.youtube.com/watch?v=inBKU0i-4Q8",
        "https://www.youtube.com/watch?v=IFI-sZfhB0k",
        "https://www.youtube.com/watch?v=IChV7-GEq4",
        "https://www.youtube.com/watch?v=1WnVJpFLj3I",
        "https://www.youtube.com/watch?v=Lsto1XFP0xc",
    ]
    video = ExpertUserVideo.objects.create(
        title=title,
        url=random.choice(urls),
        board=random_board(),
        sub_category=random_sub_category(),
        category=random_category(),
        expert=random_expert(),
        views=random.randint(1, 100),
        status="P",
    )
    for i in range(random.randint(1, 10)):
        video.likes.add(random_user())
    for i in range(random.randint(1, 10)):
        video.tags.add(random_tag())


for i in range(500):
    title = fake.paragraph()
    description = (
        fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
    )
    user_type = random.randint(0, 2)
    if user_type == 0:
        discussion = Discussion.objects.create(
            title=title,
            board=random_board(),
            sub_category=random_sub_category(),
            parent=random_parent(),
            views=random.randint(1, 100),
            status="P",
        )
    elif user_type == 1:
        discussion = Discussion.objects.create(
            title=title,
            board=random_board(),
            sub_category=random_sub_category(),
            expert=random_expert(),
            views=random.randint(1, 100),
            status="P",
        )
    elif user_type == 2:
        discussion = Discussion.objects.create(
            title=title,
            board=random_board(),
            sub_category=random_sub_category(),
            anonymous_user=fake.name(),
            views=random.randint(1, 100),
            status="P",
        )
    for i in range(random.randint(1, 10)):
        discussion.likes.add(random_user())
    for i in range(random.randint(1, 10)):
        discussion.tags.add(random_tag())


for i in range(500):
    title = fake.paragraph()
    description = (
        fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
        + fake.text()
    )
    news = News.objects.create(
        title=title,
        board=random_board(),
        views=random.randint(1, 100),
        status="P",
        is_featured=random.randint(0, 1),
    )
    for i in range(random.randint(1, 10)):
        news.tags.add(random_tag())

    for i in range(random.randint(1, 10)):
        headlines = NewsHeadline.objects.create(news=news, title=fake.text()[:149])
