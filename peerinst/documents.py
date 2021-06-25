from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import NestedField, ObjectField, TextField
from django_elasticsearch_dsl.registries import registry

from peerinst.models import Category, Discipline, Question


@registry.register_document
class QuestionDocument(Document):
    category = NestedField(
        properties={
            "title": TextField(),
        }
    )
    discipline = ObjectField(
        properties={
            "title": TextField(),
        }
    )
    id = TextField()
    user = TextField()

    def prepare_user(self, instance):
        return instance.user.username.lower() if instance.user else None

    def prepare_id(self, instance):
        return str(instance.id)

    class Index:
        name = "questions"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Question
        fields = [
            "text",
            "title",
            "type",
        ]
        related_models = [
            Category,
            Discipline,
        ]
