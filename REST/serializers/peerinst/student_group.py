from rest_framework import serializers

from peerinst.models import StudentGroup

from .dynamic_serializer import DynamicFieldsModelSerializer


class StudentGroupSerializer(DynamicFieldsModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.get_absolute_url()

    class Meta:
        model = StudentGroup
        fields = ["pk", "name", "semester", "teacher", "title", "url", "year"]
