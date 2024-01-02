from string import capwords

import bleach
from django.contrib.auth.models import User
from django.urls import reverse
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import (
    BooleanField,
    FloatField,
    IntegerField,
    KeywordField,
    NestedField,
    ObjectField,
    TextField,
)
from django_elasticsearch_dsl.registries import registry

from peerinst.models import (
    AnswerChoice,
    Category,
    Discipline,
    Question,
    QuestionFlag,
)
from peerinst.templatetags.bleach_html import ALLOWED_TAGS

from .analyzers import autocomplete, full_term, html_strip, trigram


@registry.register_document
class QuestionDocument(Document):
    """
    ElasticSearch document for Question model.

    Notes:
    - Need autocomplete type, partial, and full-word matching
    - Need to test on certain keywords: "phy", "physi", "tnagar",
      "adamsr three blocks" etc.
    - Consider "boosting" and multifields
    """

    answer_count = IntegerField(index=False)
    assignment_count = IntegerField(index=False)
    answer_style = IntegerField(index=False)
    answerchoice_set = NestedField(
        properties={
            "text": TextField(analyzer=html_strip),
        }
    )
    category = NestedField(
        properties={
            "title": TextField(
                analyzer=trigram,
            )
        }
    )  # don't break on spaces?
    collaborators = NestedField(properties={"username": TextField()})
    collections = NestedField(
        properties={
            "title": TextField(index=False),
            "url": TextField(index=False),
        }
    )
    deleted = BooleanField()
    difficulty = ObjectField(
        properties={
            "score": FloatField(index=False),
            "label": IntegerField(),
        }
    )
    discipline = ObjectField(
        properties={"title": TextField(analyzer=full_term)}
    )  # don't break on spaces?
    featured = BooleanField()
    frequency = ObjectField(
        properties={
            "first_choice": ObjectField(enabled=False),
            "second_choice": ObjectField(enabled=False),
        }
    )
    image = TextField(index=False)
    image_alt_text = TextField(index=False)
    matrix = ObjectField(enabled=False)
    most_convincing_rationales = NestedField(
        properties={
            "label": TextField(index=False),
            "text": TextField(index=False),
            "correct": BooleanField(index=False),
            "most_convincing": ObjectField(enabled=False),
        }
    )
    peer_impact = ObjectField(
        properties={
            "score": FloatField(index=False),
            "label": IntegerField(),
        }
    )
    pk = KeywordField()
    text = TextField(analyzer=html_strip)
    title = TextField(analyzer=html_strip)
    urls = ObjectField(
        properties={
            "addable_assignments": TextField(index=False),
        }
    )
    user = ObjectField(
        properties={
            "username": TextField(analyzer=autocomplete),
            "saltise": BooleanField(index=False),
            "expert": BooleanField(index=False),
        }
    )
    valid = BooleanField()
    video_url = TextField(index=False)

    def prepare_answer_count(self, instance):
        return instance.answer_count

    def prepare_assignment_count(self, instance):
        return instance.assignment_count

    def prepare_answerchoice_set(self, instance):
        if instance.answerchoice_set.count() > 0:
            return [
                {
                    "correct": instance.is_correct(i),
                    "label": ac[0],
                    "text": bleach.clean(
                        ac[1],
                        tags=ALLOWED_TAGS,
                        strip=True,
                    ).strip(),
                }
                for (i, ac) in enumerate(instance.get_choices(), 1)
            ]
        return []

    def prepare_category(self, instance):
        """Bleach and capitalize on the way out."""
        if instance.category:
            sorted_category_set = [
                capwords(
                    bleach.clean(
                        c.title,
                        tags=[],
                        strip=True,
                    ).strip()
                )
                for c in instance.category.all()
            ]

            return [{"title": c} for c in sorted_category_set]
        return []

    def prepare_collections(self, instance):
        return [
            {"title": c.title, "url": c.get_absolute_url()}
            for c in instance.collections
        ]

    def prepare_deleted(self, instance):
        return instance in type(instance).deleted_questions()

    def prepare_difficulty(self, instance):
        d = instance.get_difficulty()
        return {"score": d[0], "label": d[1]}

    def prepare_discipline(self, instance):
        """Bleach and capitalize on the way out."""
        if instance.discipline:
            return {
                "title": capwords(
                    bleach.clean(
                        instance.discipline.title,
                        tags=[],
                        strip=True,
                    ).strip()
                )
            }
        return {"title": ""}

    def prepare_featured(self, instance):
        return instance.featured

    def prepare_frequency(self, instance):
        freq = instance.get_frequency()
        return {
            "first_choice": freq["first_choice"],
            "second_choice": freq["second_choice"],
        }

    def prepare_image(self, instance):
        if instance.image:
            return str(instance.image.url)

    def prepare_matrix(self, instance):
        return instance.get_matrix()

    def prepare_most_convincing_rationales(self, instance):
        return instance.get_most_convincing_rationales()

    def prepare_peer_impact(self, instance):
        pi = instance.get_peer_impact()
        return {"score": pi[0], "label": pi[1]}

    def prepare_pk(self, instance):
        return instance.pk

    def prepare_text(self, instance):
        return bleach.clean(
            instance.text,
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

    def prepare_title(self, instance):
        return bleach.clean(
            instance.title,
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

    def prepare_urls(self, instance):
        return {
            "addable_assignments": reverse(
                "REST:teacher-assignment-for-question", args=(instance.pk,)
            ),
            "copy": reverse("teacher:question-copy", args=(instance.pk,)),
            "matrix": reverse("REST:question-matrix", args=(instance.pk,)),
            "rationales": reverse(
                "REST:question-rationales", args=(instance.pk,)
            ),
            "update": reverse("teacher:question-update", args=(instance.pk,)),
        }

    def prepare_user(self, instance):
        username = ""
        saltise = False
        expert = False
        if instance.user:
            username = instance.user.username
            if hasattr(instance.user, "saltisemember"):
                saltise = True
                expert = instance.user.saltisemember.expert
        return {
            "username": username,
            "saltise": saltise,
            "expert": expert,
        }

    def prepare_valid(self, instance):
        return (
            instance.is_not_flagged and instance.is_not_missing_answer_choices
        )

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
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "max_ngram_diff": 3,
        }

    class Django:
        model = Question
        fields = [
            "type",
        ]
        related_models = [
            AnswerChoice,
            Category,
            Discipline,
            QuestionFlag,
            User,
        ]
