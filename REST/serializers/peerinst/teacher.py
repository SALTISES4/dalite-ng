from rest_framework import serializers

from peerinst.models import Question, Teacher

from .assignment import (
    AssignmentSerializer,
    QuestionSerializer,
    UserSerializer,
)
from .dynamic_serializer import DynamicFieldsModelSerializer


class TeacherSerializer(DynamicFieldsModelSerializer):
    archived_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    assignments = AssignmentSerializer(
        fields=["editable", "pk", "question_pks", "title"],
        many=True,
        read_only=True,
        source="user.assignment_set",
    )
    deleted_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    favourite_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    questions = QuestionSerializer(
        fields=[
            "answer_count",
            "pk",
            "title",
            "type",
        ],
        many=True,
        read_only=True,
        source="user.question_set",
    )
    shared_questions = QuestionSerializer(
        fields=[
            "answer_count",
            "pk",
            "title",
            "type",
        ],
        many=True,
        read_only=True,
        source="user.collaborators",
    )
    user = UserSerializer(read_only=True)

    def validate(self, data):
        # Limit deleted questions to questions where user is owner
        questions = self.context["request"].user.question_set.all()

        if "deleted_questions" in data:
            if any([q not in questions for q in data["deleted_questions"]]):
                raise serializers.ValidationError(
                    "Cannot delete this question"
                )

        # Limit archived questions to questions where user is owner or
        # collaborator
        shared = self.context["request"].user.collaborators.all()

        if "archived_questions" in data:
            if any(
                [
                    q not in questions | shared
                    for q in data["archived_questions"]
                ]
            ):
                raise serializers.ValidationError(
                    "Cannot archive this question"
                )

        return data

    class Meta:
        model = Teacher
        fields = [
            "archived_questions",
            "assignments",
            "deleted_questions",
            "favourite_questions",
            "pk",
            "questions",
            "shared_questions",
            "user",
        ]
