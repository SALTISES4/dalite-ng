from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.fields import KeywordField
from django_elasticsearch_dsl.registries import registry

from peerinst.models import Teacher


@registry.register_document
class TeacherDocument(Document):
    username = KeywordField()

    def prepare_username(self, instance):
        return instance.user.username

    @classmethod
    def generate_id(cls, instance):
        return instance.user.username

    class Index:
        name = "teachers"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Teacher
