from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from categories.models import Board, SubCategory
from tags.models import Tagged

from .models import AdmissionInformationArticle, AdmissionInformationUserVideo, AdmissionInformationNews

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


@registry.register_document
class AdmissionInformationArticleDocument(Document):

    tags = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
        }
    )

    board = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "min_age": fields.IntegerField(),
            "max_age": fields.IntegerField(),
            "slug": fields.TextField(),
        }
    )

    sub_category = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
        }
    )

    description: fields.TextField(analyzer=html_strip)

    id = fields.IntegerField()

    timestamp = fields.DateField()

    class Index:
        name = "prod-admission-articles"

    class Django:
        model = AdmissionInformationArticle
        fields = [
            "title",
            "slug",
            "description",
            "thumbnail",
            "views",
            "status",
        ]
        related_models = [Tagged, Board, SubCategory]

        def get_queryset(self):
            return (
                super()
                .get_queryset()
                .prefetch_related("tags")
                .select_related("board", "sub_category")
            )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Board):
            return related_instance.admission_articles.all()
        if isinstance(related_instance, SubCategory):
            return related_instance.admission_articles.all()



@registry.register_document
class AdmissionInformationUserVideoDocument(Document):

    tags = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
        }
    )

    board = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "min_age": fields.IntegerField(),
            "max_age": fields.IntegerField(),
            "slug": fields.TextField(),
        }
    )

    sub_category = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
        }
    )

    id = fields.IntegerField()

    description: fields.TextField(analyzer=html_strip)

    timestamp = fields.DateField()

    class Index:
        name = "prod-admission-video"

    class Django:
        model = AdmissionInformationUserVideo
        fields = [
            "title",
            "slug",
            "description",
            "url",
            "status",
            "views",
        ]
        related_models = [Tagged, Board, SubCategory]

        def get_queryset(self):
            return (
                super()
                .get_queryset()
                .prefetch_related("tags")
                .select_related("board", "sub_category")
            )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Board):
            return related_instance.board_admission_videos.all()
        if isinstance(related_instance, SubCategory):
            return related_instance.sub_category_admission_vidoes.all()


@registry.register_document
class AdmissionInformationNewsDocument(Document):

    tags = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
        }
    )

    board = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "min_age": fields.IntegerField(),
            "max_age": fields.IntegerField(),
            "slug": fields.TextField(),
        }
    )

    id = fields.IntegerField()

    timestamp = fields.DateField()

    class Index:
        name = "prod-admission-news"

    class Django:
        model = AdmissionInformationNews
        fields = [
            "title",
            "slug",
            "content",
            "image",
            "status",
            "views",
        ]
        related_models = [Tagged, Board]

        def get_queryset(self):
            return (
                super().get_queryset().prefetch_related("tags").select_related("board")
            )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Board):
            return related_instance.board_admission_information_news.all()
