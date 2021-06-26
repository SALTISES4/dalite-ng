from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import NestedField, ObjectField, TextField
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from peerinst.models import AnswerChoice, Category, Discipline, Question

html_strip = analyzer(
    "html_strip",
    tokenizer="whitespace",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


@registry.register_document
class QuestionDocument(Document):
    answerchoice_set = NestedField(
        properties={
            "text": TextField(analyzer=html_strip),
        }
    )
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
    text = TextField(analyzer=html_strip)
    user = TextField()

    def prepare_user(self, instance):
        return instance.user.username if instance.user else None

    def prepare_id(self, instance):
        return str(instance.id)

    def get_queryset(self):
        return super().get_queryset().select_related("discipline")

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Category) or isinstance(
            related_instance, Discipline
        ):
            return related_instance.question_set.all()
        elif isinstance(related_instance, AnswerChoice):
            return related_instance.question

    class Index:
        name = "questions"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Question
        fields = [
            "title",
            "type",
        ]
        related_models = [
            AnswerChoice,
            Category,
            Discipline,
        ]
