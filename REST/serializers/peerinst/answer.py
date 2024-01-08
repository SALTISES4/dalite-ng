import bleach
from django.contrib.auth.models import User
from rest_framework import serializers

from peerinst.models import (
    Answer,
    AnswerAnnotation,
    AnswerChoice,
    ShownRationale,
    StudentGroupAssignment,
)
from peerinst.templatetags.bleach_html import ALLOWED_TAGS, STRICT_TAGS

from .assignment import QuestionSerializer
from .dynamic_serializer import DynamicFieldsModelSerializer


class AnswerSerializer(DynamicFieldsModelSerializer):
    answer_choice = serializers.SerializerMethodField()
    chosen_rationale = serializers.SerializerMethodField()
    first_answer_choice_label = serializers.SerializerMethodField()
    second_answer_choice_label = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    shown_count = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    question = QuestionSerializer(
        fields=(
            "answerchoice_set",
            "image",
            "text",
            "title",
        ),
        read_only=True,
    )

    def get_answer_choice(self, obj):
        if obj.question.type == "RO":
            return None
        else:
            return AnswerChoice.objects.filter(question=obj.question).values(
                "text", "correct"
            )[obj.first_answer_choice - 1]

    def get_chosen_rationale(self, obj):
        if obj.chosen_rationale:
            return obj.chosen_rationale.rationale
        return None

    def get_first_answer_choice_label(self, obj):
        if obj.first_answer_choice > 0:
            return obj.question.get_choice_label(obj.first_answer_choice)
        return None

    def get_second_answer_choice_label(self, obj):
        return obj.question.get_choice_label(obj.second_answer_choice)

    def get_shown_count(self, obj):
        return ShownRationale.objects.filter(shown_answer=obj).count()

    def get_timestamp(self, obj):
        return (
            obj.datetime_second if obj.datetime_second else obj.datetime_first
        )

    def get_vote_count(self, obj):
        return Answer.objects.filter(chosen_rationale_id=obj.id).count()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        keys = ["rationale", "chosen_rationale"]
        for key in keys:
            if key in ret and ret[key]:
                ret[key] = bleach.clean(
                    ret[key], tags=STRICT_TAGS, strip=True
                ).strip()
        if "answer_choice" in ret:
            if ret["answer_choice"]:
                ret["answer_choice"]["text"] = bleach.clean(
                    ret["answer_choice"]["text"],
                    tags=ALLOWED_TAGS,
                    strip=True,
                ).strip()
            else:
                ret["answer_choice"] = {"text": ""}
        return ret

    class Meta:
        model = Answer
        fields = [
            "id",
            "answer_choice",
            "assignment",
            "chosen_rationale",
            "first_answer_choice",
            "first_answer_choice_label",
            "second_answer_choice",
            "second_answer_choice_label",
            "rationale",
            "vote_count",
            "shown_count",
            "question",
            "user_token",
            "timestamp",
        ]
        read_only_fields = fields
        ordering = ["-vote_count"]


class FeedbackWriteSerialzer(serializers.ModelSerializer):
    annotator = serializers.ReadOnlyField(source="annotator.username")
    answer = serializers.PrimaryKeyRelatedField(queryset=Answer.objects.all())

    class Meta:
        model = AnswerAnnotation
        fields = ["pk", "score", "annotator", "note", "timestamp", "answer"]


class FeedbackReadSerialzer(serializers.ModelSerializer):
    annotator = serializers.ReadOnlyField(source="annotator.pk")
    answer = AnswerSerializer(
        fields=("answer_choice", "assignment", "rationale", "question")
    )

    class Meta:
        model = AnswerAnnotation
        fields = ["score", "annotator", "note", "timestamp", "answer"]


class StudentGroupAssignmentAnswerSerializer(serializers.ModelSerializer):
    """A serializer to retrieve answers from a StudentGroupAssignment."""

    answers = serializers.SerializerMethodField()

    def get_answers(self, obj):
        """
        Field will be a list of all answers for this StudentGroupAssignment for
        a single question
        """
        answers = (
            Answer.objects.filter(
                user_token__in=[
                    student.student.username
                    for student in obj.group.students.all()
                ]
            )
            .filter(assignment=obj.assignment)
            .filter(question__id=self.context["question_pk"])
        )
        answers_serialized = [
            AnswerSerializer(
                a,
                fields=(
                    "chosen_rationale",
                    "first_answer_choice_label",
                    "id",
                    "rationale",
                    "second_answer_choice_label",
                    "timestamp",
                    "user_token",
                ),
            ).data
            for a in answers
        ]
        for a in answers_serialized:
            a.update(
                {
                    "user_email": User.objects.get(
                        username=a["user_token"]
                    ).email.split("@")[0]
                }
            )
            a.pop("user_token")
        return answers_serialized

    class Meta:
        model = StudentGroupAssignment
        fields = ["pk", "answers"]
