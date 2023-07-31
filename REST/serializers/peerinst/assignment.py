import logging

import bleach
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from peerinst.models import (
    Answer,
    Assignment,
    AssignmentQuestions,
    Category,
    Collection,
    Discipline,
    Question,
    StudentGroup,
    StudentGroupAssignment,
)
from peerinst.templatetags.bleach_html import ALLOWED_TAGS

from .dynamic_serializer import DynamicFieldsModelSerializer
from .student_group import StudentGroupSerializer

logger = logging.getLogger("REST")


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
                "label": ac[0],
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
        return {"score": d[0], "label": d[1], "value": d[2]}

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
        return {"score": pi[0], "label": pi[1], "value": pi[2]}

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
            "addable_assignments": reverse(
                "REST:teacher-assignment-for-question", args=(obj.pk,)
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
            "difficulty",  # Added for new assignment interface
            "discipline",
            "frequency",
            "image",
            "image_alt_text",
            "is_owner",  # Added for new assignment interface
            "matrix",
            "peer_impact",  # Added for new assignment interface
            "pk",
            "text",
            "title",
            "urls",  # Added for new assignment interface
            "user",
        ),
    )
    question_pk = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source="question",
        required=True,
    )

    def get_unique_together_validators(self):
        """
        Have to override the unique_together constraint in order
        to support update as nested field in AssignmentSerializer
        """
        return []

    def create(self, validated_data):
        """
        Custom create method to add questions to an assignment based on pk
        Required POST data:
            - assignment (validated normally)
            - question_pk (validated normally)
        """
        assignment = validated_data["assignment"]
        question = validated_data["question"]
        if (
            assignment.editable
            and self.context["request"].user in assignment.owner.all()
        ):
            if assignment.questions.all():
                added_question = AssignmentQuestions.objects.create(
                    assignment=assignment,
                    question=question,
                    rank=assignment.questions.aggregate(
                        Max("assignmentquestions__rank")
                    )["assignmentquestions__rank__max"]
                    + 1,
                )
            else:
                added_question = AssignmentQuestions.objects.create(
                    assignment=assignment,
                    question=question,
                    rank=1,
                )
            return added_question
        raise PermissionDenied

    class Meta:
        model = AssignmentQuestions
        fields = ["assignment", "question", "question_pk", "rank", "pk"]


class AssignmentSerializer(DynamicFieldsModelSerializer):
    answer_count = serializers.ReadOnlyField()
    editable = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    is_owner = serializers.SerializerMethodField()
    owner = UserSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
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

    def get_is_owner(self, obj):
        if "request" in self.context:
            return self.context["request"].user in obj.owner.all()
        return None

    def get_question_count(self, obj):
        return obj.questions.count()

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
            "update": reverse(
                "teacher:assignment-update",
                args=(obj.pk,),
            ),
            "view": reverse(
                "teacher:assignment-detail",
                args=(obj.pk,),
            ),
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
        Only used to reorder questions and change meta data.
        Adding/deleting questions is handled by serializer for through table.
        """
        if "assignmentquestions_set" in validated_data:
            if instance.editable:
                for i, aq in enumerate(instance.assignmentquestions_set.all()):
                    aq.rank = validated_data["assignmentquestions_set"][i][
                        "rank"
                    ]
                    aq.save()

        for field in ["conclusion_page", "description", "intro_page", "title"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()

        return instance

    def to_representation(self, instance):
        """Bleach on the way out"""
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

    def to_internal_value(self, data):
        """Bleach on the way in"""
        ret = super().to_internal_value(data)
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
            "answer_count",  #
            "conclusion_page",
            "description",
            "editable",
            "intro_page",
            "is_owner",
            "is_valid",
            "owner",  #
            "pk",
            "question_count",  #
            "question_pks",
            "questions",
            "questions_basic",
            "title",
            "urls",
        ]


class StudentGroupAssignmentSerializer(DynamicFieldsModelSerializer):
    active = serializers.SerializerMethodField()
    answerCount = serializers.SerializerMethodField()
    assignment = AssignmentSerializer(fields=["pk", "urls"], read_only=True)
    assignment_pk = serializers.PrimaryKeyRelatedField(
        queryset=Assignment.objects.all(),
        source="assignment",
        required=True,
    )
    author = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    distributionState = serializers.SerializerMethodField()
    group = StudentGroupSerializer(read_only=True)
    group_pk = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(),
        source="group",
        required=True,
    )
    issueCount = serializers.SerializerMethodField()
    order = serializers.CharField(
        max_length=1000
    )  # Arbitrary upper limit as safeguard
    progress = serializers.SerializerMethodField()
    questionCount = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_active(self, obj):
        return obj.is_distributed and not obj.expired

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

    def get_assignment_pk(self, obj):
        return obj.assignment.pk

    def get_author(self, obj):
        if obj.assignment.owner.exists():
            return obj.assignment.owner.first().username
        return None

    def get_difficulty(self, obj):
        return "ToDo"  # calculate difficulty from questions

    def get_distributionState(self, obj):
        return "Distributed"
        # FIXME: choices from components/static/_localComponents/enum.ts

    def get_issueCount(self, obj):
        return 1.0  # FIXME: Do we need this?

    def get_progress(self, obj):
        return f"{100 * obj.percent_completion:.0f}"

    def get_questionCount(self, obj):
        return obj.assignment.questions.count()

    def get_title(self, obj):
        return obj.assignment.title.strip()

    def get_url(self, obj):
        return obj.get_absolute_url()

    def validate_assignment_pk(self, assignment):
        if not assignment.is_valid:
            logger.error(
                f"Assignment {assignment} is not valid and cannot be distributed."
            )
            raise serializers.ValidationError("Assignment is not valid.")
        return assignment

    def validate_due_date(self, due_date):
        """
        Check due_date is in the future
        """
        if due_date < timezone.now():
            logger.error(f"Invalid due_date: {due_date}")
            raise serializers.ValidationError(
                "Invalid due date (in the past)."
            )
        return due_date

    def validate_group_pk(self, student_group):
        """
        Check that teacher owns group and that group is "assignable"
        (see Teacher model)
        """
        teacher = self.context["request"].user.teacher

        if (
            teacher
            and teacher in student_group.teacher.all()
            and student_group in teacher.assignable_groups.all()
        ):
            return student_group

        logger.error(f"Invalid student group: {student_group}")
        raise serializers.ValidationError("Invalid student group.")

    def validate_order(self, data):
        logger.info(f"Order: {data}")
        # TODO: Reimplement custom validation in model through validators and update
        # raise serializers.ValidationError("Invalid question order.")
        return data

    def validate(self, data):
        """
        Impose unique_together on assignment and group
        """
        assignment = data["assignment"]
        group = data["group"]
        if StudentGroupAssignment.objects.filter(
            assignment=assignment, group=group
        ).exists():
            logger.error(
                f"Assignment {assignment} already distributed to {group}."
            )
            raise serializers.ValidationError(
                f"Assignment already distributed to {group}."
            )
        return data

    def create(self, validated_data):
        sga = super().create(validated_data)
        sga.distribute()
        return sga

    class Meta:
        model = StudentGroupAssignment
        fields = [
            "active",
            "answerCount",
            "assignment",
            "assignment_pk",
            "author",
            "difficulty",
            "distributionState",
            "due_date",
            "group",
            "group_pk",
            "issueCount",
            "order",
            "pk",
            "progress",
            "questionCount",
            "show_correct_answers",
            "title",
            "url",
        ]


class CollectionSerializer(DynamicFieldsModelSerializer):
    answerCount = serializers.SerializerMethodField()
    description = serializers.ReadOnlyField()
    discipline = DisciplineSerializer(read_only=True)
    follower_count = serializers.SerializerMethodField()
    title = serializers.ReadOnlyField()
    url = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True, source="owner.user")

    def get_answerCount(self, obj):
        return obj.answer_count

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_url(self, obj):
        return obj.get_absolute_url()

    class Meta:
        model = Collection
        fields = [
            "answerCount",
            "description",
            "discipline",
            "featured",
            "follower_count",
            "pk",
            "title",
            "url",
            "user",
        ]
