from rest_framework import serializers

from peerinst.models import Question, Teacher

from .assignment import AssignmentSerializer, UserSerializer
from .dynamic_serializer import DynamicFieldsModelSerializer


class TeacherSerializer(DynamicFieldsModelSerializer):
    assignments = AssignmentSerializer(
        fields=["editable", "pk", "question_pks", "title"],
        many=True,
        read_only=True,
        source="user.assignment_set",
    )
    favourite_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    user = UserSerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = ["pk", "assignments", "favourite_questions", "user"]
