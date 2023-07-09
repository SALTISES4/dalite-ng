from django.utils import timezone
from rest_framework import serializers

from peerinst.models import (
    Assignment,
    Collection,
    Question,
    StudentGroupAssignment,
    Teacher,
)

from .assignment import (
    AssignmentSerializer,
    QuestionSerializer,
    UserSerializer,
)
from .dynamic_serializer import DynamicFieldsModelSerializer


class TeacherSerializer(DynamicFieldsModelSerializer):
    activeAssignmentCount = serializers.SerializerMethodField()
    activeGroupCount = serializers.SerializerMethodField()
    archived_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    assignments = AssignmentSerializer(
        fields=[
            "editable",
            "is_valid",
            "pk",
            "questions_basic",
            "question_pks",
            "title",
            "urls",
        ],
        many=True,
        read_only=True,
    )
    # For updating
    assignment_pks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Assignment.objects.all(), source="assignments"
    )
    # Allows updating
    bookmarked_collections = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Collection.objects.all(),
        source="followers",
    )
    createdQuestionCount = serializers.SerializerMethodField()
    current_groups = serializers.SerializerMethodField()
    deleted_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    favourite_questions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Question.objects.all()
    )
    owned_assignments = AssignmentSerializer(
        fields=["editable", "is_valid", "pk", "question_pks", "title", "urls"],
        many=True,
        read_only=True,
        source="user.assignment_set",
    )
    questions = QuestionSerializer(
        fields=[
            "answer_count",
            "is_editable",
            "is_valid",
            "pk",
            "title",
            "type",
            "urls",
        ],
        many=True,
        read_only=True,
        source="user.question_set",
    )
    shared_questions = QuestionSerializer(
        fields=[
            "answer_count",
            "is_editable",
            "is_valid",
            "pk",
            "title",
            "type",
            "urls",
        ],
        many=True,
        read_only=True,
        source="user.collaborators",
    )
    user = UserSerializer(read_only=True)

    def get_activeAssignmentCount(self, obj):
        now = timezone.now()
        return (
            StudentGroupAssignment.objects.filter(
                group__in=obj.current_groups.all()
            )
            .filter(distribution_date__lt=now)
            .filter(due_date__gt=now)
            .count()
        )

    def get_activeGroupCount(self, obj):
        return obj.current_groups.count()

    def get_createdQuestionCount(self, obj):
        return Question.objects.filter(user=obj.user).count()

    def get_current_groups(self, obj):
        return [
            {
                "pk": g.pk,
                "name": g.name,
                "title": g.title,
                "semester": g.semester,
                "year": g.year,
            }
            for g in obj.current_groups.all()
        ]

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
            "activeAssignmentCount",
            "activeGroupCount",
            "archived_questions",
            "assignment_pks",
            "assignments",
            "bookmarked_collections",
            "createdQuestionCount",
            "current_groups",
            "deleted_questions",
            "favourite_questions",
            "owned_assignments",
            "pk",
            "questions",
            "shared_questions",
            "user",
        ]
