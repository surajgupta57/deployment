from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from categories.models import Board, SubCategory
from tags.models import Tagged

from .models import ExpertArticle

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


@registry.register_document
class ExpertArticleDocument(Document):

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
        name = "prod-expert-articles"

    class Django:
        model = ExpertArticle
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
            return related_instance.expert_articles.all()
        if isinstance(related_instance, SubCategory):
            return related_instance.expert_articles.all()
