import bleach
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import (
    BooleanField,
    IntegerField,
    KeywordField,
    NestedField,
    ObjectField,
    TextField,
)
from django_elasticsearch_dsl.registries import registry

from peerinst.models import Collection
from peerinst.templatetags.bleach_html import ALLOWED_TAGS

from .analyzers import autocomplete, full_term, html_strip


@registry.register_document
class CollectionDocument(Document):
    answerCount = IntegerField(index=False)
    description = TextField(analyzer=html_strip)
    discipline = ObjectField(
        properties={"title": TextField(analyzer=full_term)}
    )
    follower_count = IntegerField(index=False)
    pk = KeywordField(index=False)
    public = BooleanField()
    title = TextField(analyzer=html_strip)
    user = NestedField(
        properties={"username": TextField(analyzer=autocomplete)}
    )

    def prepare_answerCount(self, instance):
        return instance.answer_count

    def prepare_description(self, instance):
        return bleach.clean(
            instance.description or "",
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

    def prepare_discipline(self, instance):
        """Bleach"""
        if instance.discipline:
            return {
                "title": bleach.clean(
                    instance.discipline.title,
                    tags=[],
                    strip=True,
                ).strip()
            }
        return {"title": ""}

    def prepare_follower_count(self, instance):
        return instance.followers.count()

    def prepare_public(self, instance):
        return not instance.private

    def prepare_title(self, instance):
        return bleach.clean(
            instance.title,
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

    def prepare_user(self, instance):
        username = ""
        saltise = False
        expert = False
        if instance.owner:
            username = instance.owner.user.username
            if hasattr(instance.owner.user, "saltisemember"):
                saltise = True
                expert = instance.owner.user.saltisemember.expert
        return {
            "username": username,
            "saltise": saltise,
            "expert": expert,
        }

    class Index:
        name = "collections"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Collection
