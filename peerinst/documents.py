import bleach
from django.contrib.auth.models import User
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import (
    BooleanField,
    IntegerField,
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
from peerinst.templatetags.bleach_html import ALLOWED_TAGS

html_strip = analyzer(
    "html_strip",
    tokenizer="whitespace",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


@registry.register_document
class QuestionDocument(Document):
    answer_count = IntegerField()
    answerchoice_set = NestedField(
        properties={
            "text": TextField(analyzer=html_strip),
        }
    )
    category = NestedField(properties={"title": TextField()})
    collaborators = NestedField(properties={"username": TextField()})
    difficulty = ObjectField()
    discipline = ObjectField(properties={"title": TextField()})
    id = TextField()
    text = TextField(analyzer=html_strip)
    questionflag_set = BooleanField()
    user = ObjectField(properties={"username": TextField()})
    valid = BooleanField()

    def prepare_answer_count(self, instance):
        """
        TODO: Refactor to model
        """
        return instance.answer_set.count()

    def prepare_answerchoice_set(self, instance):
        if instance.answerchoice_set.count() > 0:
            return [
                {
                    "text": bleach.clean(
                        ac.text,
                        tags=ALLOWED_TAGS,
                        styles=[],
                        strip=True,
                    )
                }
                for ac in instance.answerchoice_set.all()
            ]

    def prepare_category(self, instance):
        if instance.category:
            return [
                {
                    "title": bleach.clean(
                        c.title,
                        tags=ALLOWED_TAGS,
                        styles=[],
                        strip=True,
                    )
                }
                for c in instance.category.all()
            ]

    def prepare_difficulty(self, instance):
        return instance.get_matrix()

    def prepare_discipline(self, instance):
        if instance.discipline:
            return {
                "title": bleach.clean(
                    instance.discipline.title,
                    tags=ALLOWED_TAGS,
                    styles=[],
                    strip=True,
                )
            }

    def prepare_id(self, instance):
        return str(instance.id)

    def prepare_questionflag_set(self, instance):
        """Replicate logic for UnflaggedQuestionManager"""
        return (
            any(instance.questionflag_set.all())
            if instance.questionflag_set.exists()
            else False
        )

    def prepare_text(self, instance):
        return bleach.clean(
            instance.text,
            tags=ALLOWED_TAGS,
            styles=[],
            strip=True,
        )

    def prepare_title(self, instance):
        return bleach.clean(
            instance.title,
            tags=ALLOWED_TAGS,
            styles=[],
            strip=True,
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
