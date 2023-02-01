import bleach
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import serializers
from rest_framework.exceptions import bad_request

from peerinst.models import (
    Answer,
    Assignment,
    AssignmentQuestions,
    Category,
    Discipline,
    Question,
    StudentGroupAssignment,
)
from peerinst.templatetags.bleach_html import ALLOWED_TAGS

from .dynamic_serializer import DynamicFieldsModelSerializer
from .student_group import StudentGroupSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["title"]

    def to_representation(self, instance):
        """Bleach"""
        ret = super().to_representation(instance)
        ret["title"] = bleach.clean(ret["title"], tags=[], strip=True).strip()
        return ret


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ["title", "pk"]

    def to_representation(self, instance):
        """Bleach"""
        ret = super().to_representation(instance)
        ret["title"] = bleach.clean(ret["title"], tags=[], strip=True).strip()
        return ret


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class QuestionSerializer(DynamicFieldsModelSerializer):
    answer_count = serializers.ReadOnlyField()
    answerchoice_set = serializers.SerializerMethodField()
    assignment_count = serializers.ReadOnlyField()
    category = CategorySerializer(many=True, read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    difficulty = serializers.SerializerMethodField()
    discipline = DisciplineSerializer(read_only=True)
    flag_reasons = serializers.ReadOnlyField()
    frequency = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()
    is_not_flagged = serializers.ReadOnlyField()
    is_not_missing_answer_choices = serializers.ReadOnlyField()
    is_not_missing_expert_rationale = serializers.ReadOnlyField()
    is_not_missing_sample_answers = serializers.ReadOnlyField()
    is_owner = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    matrix = serializers.SerializerMethodField()
    most_convincing_rationales = serializers.SerializerMethodField()
    peer_impact = serializers.SerializerMethodField()
    urls = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)

    def get_answerchoice_set(self, obj):
        return [
            {
                "correct": obj.is_correct(i),
                "text": bleach.clean(
                    ac[1],
                    tags=ALLOWED_TAGS,
                    strip=True,
                ).strip(),
            }
            for i, ac in enumerate(obj.get_choices(), 1)
        ]

    def get_difficulty(self, obj):
        d = obj.get_difficulty()
        # TODO: check how value gets out and update component
        return {"score": d[0], "label": d[1]}

    def get_frequency(self, obj):
        return obj.get_frequency()

    def get_is_editable(self, obj):
        if "request" in self.context:
            return obj.is_editable and (
                self.context["request"].user == obj.user
                or self.context["request"].user in obj.collaborators.all()
            )
        return obj.is_editable

    def get_is_owner(self, obj):
        if "request" in self.context:
            return (
                self.context["request"].user == obj.user
                or self.context["request"].user in obj.collaborators.all()
            )
        return False

    def get_matrix(self, obj):
        return obj.get_matrix()

    def get_most_convincing_rationales(self, obj):
        return obj.get_most_convincing_rationales()

    def get_peer_impact(self, obj):
        pi = obj.get_peer_impact()
        return {"score": pi[0], "label": pi[1]}

    def get_urls(self, obj):
        return {
            "add_answer_choices": reverse(
                "answer-choice-form", args=(obj.pk,)
            ),
            "add_expert_rationales": reverse(
                "research-fix-expert-rationale", args=(obj.pk,)
            ),
            "add_new_question": reverse("question-create"),
            "add_sample_answers": reverse(
                "sample-answer-form", args=(obj.pk,)
            ),
            "copy_question": reverse("question-clone", args=(obj.pk,)),
            "fix": reverse("question-fix", args=(obj.pk,)),
        }

    class Meta:
        model = Question
        fields = [
            "answer_count",
            "answerchoice_set",
            "answer_style",
            "assignment_count",
            "category",
            "collaborators",
            "difficulty",
            "discipline",
            "flag_reasons",
            "frequency",
            "image",
            "image_alt_text",
            "is_editable",
            "is_not_flagged",
            "is_not_missing_answer_choices",
            "is_not_missing_expert_rationale",
            "is_not_missing_sample_answers",
            "is_owner",
            "is_valid",
            "matrix",
            "most_convincing_rationales",
            "peer_impact",
            "pk",
            "text",
            "title",
            "type",
            "urls",
            "user",
            "video_url",
        ]

    def to_representation(self, instance):
        """Bleach HTML-supported fields"""
        ret = super().to_representation(instance)
        if "title" in ret:
            ret["title"] = bleach.clean(
                ret["title"], tags=ALLOWED_TAGS, strip=True
            ).strip()
        if "text" in ret:
            ret["text"] = bleach.clean(
                ret["text"], tags=ALLOWED_TAGS, strip=True
            ).strip()
        return ret


class RankSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(
        read_only=True,
        fields=(
            "answer_count",
            "answerchoice_set",
            "category",
            "collaborators",
            "discipline",
            "frequency",
            "image",
            "image_alt_text",
            "matrix",
            "pk",
            "text",
            "title",
            "user",
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


class AssignmentSerializer(DynamicFieldsModelSerializer):
    editable = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    question_pks = serializers.SerializerMethodField()
    questions = RankSerializer(
        source="assignmentquestions_set",
        many=True,
        required=False,
    )
    questions_basic = QuestionSerializer(
        fields=[
            "answer_count",
            "pk",
            "title",
            "type",
        ],
        many=True,
        read_only=True,
        source="questions",
    )
    urls = serializers.SerializerMethodField()

    def get_question_pks(self, obj):
        return list(obj.questions.values_list("pk", flat=True))

    def get_urls(self, obj):
        return {
            "copy": reverse("assignment-copy", args=(obj.pk,)),
            "distribute": reverse(
                "student-group-assignment-create", args=(obj.pk,)
            ),
            "fix": reverse(
                "assignment-fix",
                args=(obj.pk,),
            ),
            "preview": obj.get_absolute_url(),
            "update": reverse("assignment-update", args=(obj.pk,)),
        }

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

    def create(self, validated_data):
        """Attach user and add to teacher assignments"""
        assignment = super().create(validated_data)
        assignment.owner.add(self.context["request"].user)
        self.context["request"].user.teacher.assignments.add(assignment)
        return assignment

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
        """Bleach fields"""
        ret = super().to_representation(instance)
        for field in ["conclusion_page", "description", "intro_page"]:
            if field in ret and ret[field]:
                ret[field] = bleach.clean(
                    ret[field], tags=ALLOWED_TAGS, strip=True
                ).strip()
        for field in ["title"]:
            if field in ret and ret[field]:
                ret[field] = bleach.clean(
                    ret[field], tags=[], strip=True
                ).strip()
        return ret

    class Meta:
        model = Assignment
        fields = [
            "conclusion_page",
            "description",
            "editable",
            "intro_page",
            "is_valid",
            "pk",
            "question_pks",
            "questions",
            "questions_basic",
            "title",
            "urls",
        ]


class GroupAssignmentSerializer(DynamicFieldsModelSerializer):
    author = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    distributionState = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    questionCount = serializers.SerializerMethodField()
    answerCount = serializers.SerializerMethodField()
    title = serializers.ReadOnlyField()
    dueDate = serializers.ReadOnlyField()
    issueCount = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    def get_author(self, obj):
        return obj.assignment.owner.first().username

    def get_difficulty(self, obj):
        return "ToDo"  # calculate difficulty from questions

    def get_distributionState(self, obj):
        return "Distributed"
        # FIXME: choices from components/static/_localComponents/enum.ts

    def get_groups(self, obj):
        return StudentGroupSerializer(obj.group).data
        # expected type is list?

    def get_questionCount(self, obj):
        return obj.assignment.questions.count()

    def get_answerCount(self, obj):
        return (
            Answer.objects.filter(
                user_token__in=[
                    student.student.username
                    for student in obj.group.students.all()
                ]
            )
            .filter(assignment=obj.assignment)
            .count()
        )

    def get_issueCount(self, obj):
        return 1.0  # FIXME

    def get_progress(self, obj):
        return 1.0  # FIXME

    class Meta:
        model = StudentGroupAssignment
        fields = [
            "author",
            "difficulty",
            "distributionState",
            "groups",
            "questionCount",
            "answerCount",
            "title",
            "dueDate",
            "issueCount",
            "progress",
        ]
