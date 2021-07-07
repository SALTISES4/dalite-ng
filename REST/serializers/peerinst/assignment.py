import bleach
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import title
from rest_framework import serializers
from rest_framework.exceptions import bad_request

from peerinst.models import (
    Assignment,
    AssignmentQuestions,
    Category,
    Discipline,
    Question,
)
from peerinst.templatetags.bleach_html import ALLOWED_TAGS

from .dynamic_serializer import DynamicFieldsModelSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["title"]

    def to_representation(self, instance):
        """Bleach and ensure title case"""
        ret = super().to_representation(instance)
        ret["title"] = title(
            bleach.clean(ret["title"], tags=[], styles=[], strip=True)
        )
        return ret


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ["title", "pk"]

    def to_representation(self, instance):
        """Bleach and ensure title case"""
        ret = super().to_representation(instance)
        ret["title"] = title(
            bleach.clean(ret["title"], tags=[], styles=[], strip=True)
        )
        return ret


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class QuestionSerializer(DynamicFieldsModelSerializer):
    answer_count = serializers.SerializerMethodField()
    category = CategorySerializer(many=True, read_only=True)
    choices = serializers.SerializerMethodField()
    discipline = DisciplineSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    most_convincing_rationales = serializers.SerializerMethodField()
    matrix = serializers.SerializerMethodField()
    freq = serializers.SerializerMethodField()
    collaborators = UserSerializer(many=True, read_only=True)

    def get_answer_count(self, obj):
        return obj.answer_set.count()

    def get_choices(self, obj):
        return obj.get_choices()

    def get_most_convincing_rationales(self, obj):
        return obj.get_most_convincing_rationales()

    def get_matrix(self, obj):
        return obj.get_matrix()

    def get_freq(self, obj):
        return obj.get_frequency()

    class Meta:
        model = Question
        fields = [
            "pk",
            "title",
            "text",
            "user",
            "discipline",
            "answer_count",
            "category",
            "image",
            "image_alt_text",
            "choices",
            "most_convincing_rationales",
            "matrix",
            "freq",
            "collaborators",
        ]

    def to_representation(self, instance):
        """Bleach HTML-supported fields"""
        ret = super().to_representation(instance)
        if "title" in ret:
            ret["title"] = bleach.clean(
                ret["title"], tags=ALLOWED_TAGS, styles=[], strip=True
            )
        if "text" in ret:
            ret["text"] = bleach.clean(
                ret["text"], tags=ALLOWED_TAGS, styles=[], strip=True
            ).strip()
        if "choices" in ret:
            ret["choices"] = [
                (
                    choice[0],
                    bleach.clean(
                        choice[1], tags=ALLOWED_TAGS, styles=[], strip=True
                    ).strip(),
                    instance.is_correct(i),
                )
                for (i, choice) in enumerate(ret["choices"], 1)
            ]
        return ret


class RankSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(
        read_only=True,
        fields=(
            "pk",
            "title",
            "text",
            "user",
            "discipline",
            "answer_count",
            "category",
            "image",
            "image_alt_text",
            "choices",
            "matrix",
            "freq",
            "collaborators",
        ),
    )

    def create(self, validated_data):
        """Custom create method to add questions to an assignment based on pk
        Required POST data:
            - assignment (validated normally)
            - question_pk (validated here)
        """

        assignment = validated_data["assignment"]
        if (
            assignment.editable
            and self.context["request"].user in assignment.owner.all()
        ):
            if "question_pk" in self.context["request"].data:
                question_pk = self.context["request"].data["question_pk"]
                if assignment.questions.all():
                    added_question = AssignmentQuestions.objects.create(
                        assignment=assignment,
                        question=get_object_or_404(Question, pk=question_pk),
                        rank=assignment.questions.aggregate(
                            Max("assignmentquestions__rank")
                        )["assignmentquestions__rank__max"]
                        + 1,
                    )
                else:
                    added_question = AssignmentQuestions.objects.create(
                        assignment=assignment,
                        question=get_object_or_404(Question, pk=question_pk),
                        rank=1,
                    )
                if added_question:
                    return added_question
                else:
                    raise bad_request
            else:
                raise bad_request
        raise PermissionDenied

    class Meta:
        model = AssignmentQuestions
        fields = ["assignment", "question", "rank", "pk"]


class AssignmentSerializer(serializers.ModelSerializer):
    questions = RankSerializer(source="assignmentquestions_set", many=True)

    def validate_questions(self, data):
        assignment_questions = list(
            self.instance.assignmentquestions_set.all()
        )
        if len(data) == len(assignment_questions):
            return data
        else:
            raise serializers.ValidationError(
                "Question list must contain all questions from this assignment"
            )

    def update(self, instance, validated_data):
        """
        Only used to reorder questions.
        Adding/deleting questions is handled by serializer for through table.
        """
        if instance.editable:
            for i, aq in enumerate(instance.assignmentquestions_set.all()):
                aq.rank = validated_data["assignmentquestions_set"][i]["rank"]
                aq.save()

            return instance
        raise PermissionDenied

    def to_representation(self, instance):
        """Bleach HTML-supported fields"""
        ret = super().to_representation(instance)
        if "title" in ret:
            ret["title"] = bleach.clean(
                ret["title"], tags=ALLOWED_TAGS, styles=[], strip=True
            )
        return ret

    class Meta:
        model = Assignment
        fields = ["title", "questions"]
