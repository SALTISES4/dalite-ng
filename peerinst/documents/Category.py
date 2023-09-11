from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import TextField
from django_elasticsearch_dsl.registries import registry

from peerinst.models import Category

from .analyzers import full_term


@registry.register_document
class CategoryDocument(Document):
    title = TextField(analyzer=full_term)

    class Index:
        name = "categories"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Category
