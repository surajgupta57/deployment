from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from categories.models import Board
from tags.models import Tagged

from .models import News

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["standard", "lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


@registry.register_document
class NewsDocument(Document):

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
        name = "prod-news"

    class Django:
        model = News
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
            return related_instance.board_videos.all()
