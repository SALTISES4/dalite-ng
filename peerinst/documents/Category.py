from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import SearchAsYouTypeField, TextField
from django_elasticsearch_dsl.registries import registry

from peerinst.models import Category


@registry.register_document
class CategoryDocument(Document):
    title = TextField(
        fields={
            "raw": SearchAsYouTypeField(),
        },
    )

    class Index:
        name = "categories"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Category
