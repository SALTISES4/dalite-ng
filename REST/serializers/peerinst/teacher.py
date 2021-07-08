from rest_framework import serializers

from peerinst.models import Question, Teacher

from .assignment import UserSerializer
from .dynamic_serializer import DynamicFieldsModelSerializer


class TeacherSerializer(DynamicFieldsModelSerializer):
    favourite_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    user = UserSerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = ["pk", "favourite_questions", "user"]
