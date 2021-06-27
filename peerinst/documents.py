from django.contrib.auth.models import User
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import (
    BooleanField,
    NestedField,
    ObjectField,
    TextField,
)
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from peerinst.models import (
    AnswerChoice,
    Category,
    Collection,
    Discipline,
    Question,
    QuestionFlag,
)

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
    category = NestedField(properties={"title": TextField()})
    collaborators = NestedField(properties={"username": TextField()})
    discipline = ObjectField(properties={"title": TextField()})
    id = TextField()
    text = TextField(analyzer=html_strip)
    questionflag_set = BooleanField()
    user = ObjectField(properties={"username": TextField()})
    valid = BooleanField()

    def prepare_id(self, instance):
        return str(instance.id)

    def prepare_questionflag_set(self, instance):
        """Replicate logic for UnflaggedQuestionManager"""
        return (
            any(instance.questionflag_set.all())
            if instance.questionflag_set.exists()
            else False
        )

    def prepare_valid(self, instance):
        """
        Replicate valid question logic

        TODO: Refactor to model
        """
        return instance.answerchoice_set.count() > 0 or instance.type == "RO"

    def get_queryset(self):
        return super().get_queryset().select_related("discipline", "user")

    def get_instances_from_related(self, related_instance):
        for model in [Category, Discipline, User]:
            if isinstance(related_instance, model):
                return related_instance.question_set.all()
        for model in [AnswerChoice, QuestionFlag]:
            if isinstance(related_instance, model):
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
            QuestionFlag,
            User,
        ]


@registry.register_document
class CollectionDocument(Document):
    discipline = ObjectField(properties={"title": TextField()})

    class Index:
        name = "collections"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Collection
        fields = ["title", "private", "featured"]
