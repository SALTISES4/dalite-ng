from peerinst.models import StudentGroup

from .dynamic_serializer import DynamicFieldsModelSerializer


class StudentGroupSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StudentGroup
        fields = ["pk", "teacher", "title"]
