import bleach
from django.urls import reverse
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import (
    IntegerField,
    KeywordField,
    NestedField,
    ObjectField,
    TextField,
)
from django_elasticsearch_dsl.registries import registry

from elastic.documents.analyzers import autocomplete, html_strip
from peerinst.models import Assignment, Question
from peerinst.templatetags.bleach_html import ALLOWED_TAGS


@registry.register_document
class AssignmentDocument(Document):
    answer_count = IntegerField(index=False)
    description = TextField(analyzer=html_strip)
    owner = NestedField(
        properties={"username": TextField(analyzer=autocomplete)}
    )
    pk = KeywordField(index=False)
    question_count = IntegerField(index=False)
    title = TextField(analyzer=html_strip)
    urls = ObjectField(
        properties={
            "preview": TextField(index=False),
            "update": TextField(index=False),
        }
    )

    def prepare_answer_count(self, instance):
        return instance.answer_count

    def prepare_description(self, instance):
        return bleach.clean(
            instance.description or "",
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

    def prepare_pk(self, instance):
        return instance.pk

    def prepare_question_count(self, instance):
        return instance.questions.count()

    def prepare_title(self, instance):
        return bleach.clean(
            instance.title,
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

    def prepare_urls(self, instance):
        return {
            "preview": instance.get_absolute_url(),
            "update": reverse(
                "teacher:assignment-update",
                args=(instance.pk,),
            ),
        }

    def get_instances_from_related(self, related_instance):
        for model in [Question]:
            if isinstance(related_instance, model):
                return related_instance.assignment_set.all()

    class Index:
        name = "assignments"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Assignment
        related_models = [Question]
