import bleach
from django.contrib.auth.models import User
from django.template.defaultfilters import title
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import (
    BooleanField,
    FloatField,
    IntegerField,
    NestedField,
    ObjectField,
    TextField,
)
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer, token_filter, tokenizer

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

full_term = analyzer("full_term", tokenizer="keyword", filter=["lowercase"])

autocomplete = analyzer(
    "autocomplete",
    tokenizer=tokenizer("autocomplete", "edge_ngram", min_gram=3, max_gram=50),
    filter=["lowercase"],
)

trigram_filter = token_filter("ngram", "ngram", min_gram=3, max_gram=3)
trigram = analyzer(
    "trigram", tokenizer="whitespace", filter=["lowercase", trigram_filter]
)


@registry.register_document
class QuestionDocument(Document):
    """
    Notes:
    - Need both autocomplete type matching, partial matching, and full-word
      matching
    - Need to test on certain keywords: "phy", "physi", "tnagar",
      "adamsr three blocks" etc.
    - Consider "boosting" and multifields
    """

    answer_count = IntegerField(index=False)
    assignment_count = IntegerField()
    answer_style = IntegerField(index=False)
    answerchoice_set = NestedField(
        properties={
            "text": TextField(analyzer=html_strip),
        }
    )
    category = NestedField(
        properties={
            "title": TextField(
                analyzer=autocomplete,
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
    difficulty = ObjectField(
        properties={
            "score": FloatField(index=False),
            "label": TextField(analyzer=full_term),
        }
    )
    discipline = ObjectField(
        properties={"title": TextField(analyzer=autocomplete)}
    )  # don't break on spaces?
    featured = BooleanField()
    frequency = ObjectField(
        properties={
            "first_choice": ObjectField(enabled=False),
            "second_choice": ObjectField(enabled=False),
        }
    )
    id = TextField()
    image = TextField(index=False)
    image_alt_text = TextField(index=False)
    matrix = ObjectField(enabled=False)
    peer_impact = ObjectField(
        properties={
            "score": FloatField(index=False),
            "label": TextField(analyzer=full_term),
        }
    )
    text = TextField(analyzer=html_strip)
    questionflag_set = BooleanField()
    user = ObjectField(
        properties={"username": TextField(analyzer=autocomplete)}
    )
    valid = BooleanField()
    deleted = BooleanField()
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
                    "text": bleach.clean(
                        ac[1],
                        tags=ALLOWED_TAGS,
                        styles=[],
                        strip=True,
                    ),
                }
                for i, ac in enumerate(instance.get_choices(), 1)
            ]
        return []

    def prepare_category(self, instance):
        """Bleach and ensure title case"""
        if instance.category:
            sorted_category_set = [
                title(
                    bleach.clean(
                        c.title,
                        tags=[],
                        styles=[],
                        strip=True,
                    )
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
        return {"score": d[0], "label": str(d[1])}

    def prepare_discipline(self, instance):
        """Bleach and ensure title case"""
        if instance.discipline:
            return {
                "title": title(
                    bleach.clean(
                        instance.discipline.title,
                        tags=[],
                        styles=[],
                        strip=True,
                    )
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

    def prepare_id(self, instance):
        return str(instance.id)

    def prepare_image(self, instance):
        return str(instance.image)

    def prepare_matrix(self, instance):
        return instance.get_matrix()

    def prepare_peer_impact(self, instance):
        pi = instance.get_peer_impact()
        return {"score": pi[0], "label": str(pi[1])}

    def prepare_questionflag_set(self, instance):
        return Question.flagged_objects.filter(pk=instance.pk).exists()

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

        TODO:
            - Refactor to model
            - Also, need to add a check that there are enough sample answers!
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
