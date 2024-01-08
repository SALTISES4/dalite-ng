import bleach
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import SearchAsYouTypeField, TextField
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from peerinst.models import Category


@registry.register_document
class CategoryDocument(Document):
    """ElasticSearch document for Category model."""

    title = TextField(
        fields={
            "raw": SearchAsYouTypeField(
                analyzer=analyzer(
                    "search-as-you-type",
                    tokenizer="standard",
                    filter=["lowercase"],
                ),
            ),
        },
    )

    def prepare_title(self, instance):
        """Bleach on the way out."""
        return bleach.clean(
            instance.title,
            tags=[],
            strip=True,
        ).strip()

    class Index:
        name = "categories"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Category
