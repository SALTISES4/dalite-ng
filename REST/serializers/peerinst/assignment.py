import logging
from string import capwords

import bleach
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from PIL import Image
from rest_framework import serializers

from peerinst.documents import CategoryDocument
from peerinst.forms import RichTextRationaleField
from peerinst.models import (
    Answer,
    AnswerChoice,
    Assignment,
    AssignmentQuestions,
    Category,
    Collection,
    Discipline,
    Question,
    StudentGroup,
    StudentGroupAssignment,
)
from peerinst.templatetags.bleach_html import ALLOWED_TAGS, STRICT_TAGS

from .dynamic_serializer import DynamicFieldsModelSerializer
from .student_group import StudentGroupSerializer

logger = logging.getLogger("REST")


class CategorySerializer(DocumentSerializer):
    def to_representation(self, instance):
        """Bleach and capitalize on the way out."""
        ret = super().to_representation(instance)
        ret["title"] = capwords(
            bleach.clean(ret["title"], tags=[], strip=True).strip()
        )
        return ret

    class Meta:
        document = CategoryDocument
        fields = ["title"]


class DisciplineSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        """Bleach on the way out."""
        ret = super().to_representation(instance)
        ret["title"] = capwords(
            bleach.clean(ret["title"], tags=[], strip=True).strip()
        )
        return ret

    class Meta:
        model = Discipline
        fields = ["title", "pk"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class SampleAnswerSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(read_only=False, required=False)

    def validate_rationale(self, value):
        """Run validators in peerinst/forms.py for RichTextRationaleField."""
        for validator in RichTextRationaleField.default_validators:
            validator(value)
        return value

    def to_representation(self, instance):
        """Bleach on the way out."""
        ret = super().to_representation(instance)
        if "rationale" in ret and ret["rationale"]:
            ret["rationale"] = bleach.clean(
                ret["rationale"], tags=STRICT_TAGS, strip=True
            ).strip()
        return ret

    class Meta:
        model = Answer
        fields = [
            "expert",
            "pk",
            "rationale",
        ]
        read_only_fields = ["pk"]


class AnswerChoiceSerializer(DynamicFieldsModelSerializer):
    pk = serializers.IntegerField(required=False)
    expert_answers = SampleAnswerSerializer(many=True, required=False)
    sample_answers = SampleAnswerSerializer(many=True)

    def validate(self, data):
        """Check correct answer choices have an expert rationale."""
        if data["correct"] and (
            "expert_answers" not in data or len(data["expert_answers"]) == 0
        ):
            raise serializers.ValidationError(
                _(
                    "An expert rationale is required for each correct answer choice"  # noqa E501
                )
            )

        """Check each answer choice has at least one sample rationale."""
        if len(data["sample_answers"]) == 0:
            raise serializers.ValidationError(
                _("An sample rationale is required for each answer choice")
            )
        return data

    def to_representation(self, instance):
        """Bleach on the way out."""
        ret = super().to_representation(instance)
        if "text" in ret and ret["text"]:
            ret["text"] = bleach.clean(
                ret["text"], tags=ALLOWED_TAGS, strip=True
            ).strip()
        return ret

    class Meta:
        model = AnswerChoice
        fields = [
            "correct",
            "expert_answers",
            "pk",
            "question",
            "sample_answers",
            "text",
        ]


class NullableM2MFormDataSerializer(serializers.SlugRelatedField):
    """
    Serializer for handling nullable many-to-many fields in form data.

    Args:
        data: The input data to be converted to internal value.

    Returns:
        The internal value of the many-to-many field, or None if data is "[]".
    """

    def to_internal_value(self, data):
        return None if data == "[]" else super().to_internal_value(data)


class NullablePrimaryKeyFormDataSerializer(serializers.PrimaryKeyRelatedField):
    """
    Serializer for handling nullable primary key related fields in form data.

    Args:
        data: The input data to be converted to internal value.

    Returns:
        The internal value of the primary key field, or None if data is "null".
    """

    def to_internal_value(self, data):
        return None if data == "null" else super().to_internal_value(data)


class QuestionSerializer(DynamicFieldsModelSerializer):
    """Question model serializer with dynamic field filtering via querystring."""

    answer_count = serializers.ReadOnlyField()
    answerchoice_set = AnswerChoiceSerializer(
        fields=[
            "correct",
            "expert_answers",
            "pk",
            "sample_answers",
            "text",
        ],
        many=True,
        required=False,
    )
    assignment_count = serializers.ReadOnlyField()
    category = CategorySerializer(many=True, read_only=True)
    category_pk = NullableM2MFormDataSerializer(
        queryset=Category.objects.all(),
        slug_field="title",
        many=True,
        source="category",
        allow_null=True,
        required=False,
    )
    collaborators = UserSerializer(many=True, read_only=True)
    collaborators_pk = NullableM2MFormDataSerializer(
        queryset=User.objects.filter(teacher__isnull=False),
        slug_field="username",
        many=True,
        source="collaborators",
        allow_null=True,
        required=False,
    )
    difficulty = serializers.SerializerMethodField()
    discipline = DisciplineSerializer(read_only=True)
    discipline_pk = NullablePrimaryKeyFormDataSerializer(
        queryset=Discipline.objects.all(),
        many=False,
        source="discipline",
        allow_null=True,
        required=False,
    )
    flag_reasons = serializers.ReadOnlyField()
    frequency = serializers.ReadOnlyField(source="get_frequency")
    image = serializers.ImageField(
        allow_empty_file=True,
        allow_null=True,
        required=False,
    )
    is_editable = serializers.SerializerMethodField()
    is_not_flagged = serializers.ReadOnlyField()
    is_not_missing_answer_choices = serializers.ReadOnlyField()
    is_not_missing_expert_rationale = serializers.ReadOnlyField()
    is_not_missing_sample_answers = serializers.ReadOnlyField()
    is_owner = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    matrix = serializers.ReadOnlyField(source="get_matrix")
    most_convincing_rationales = serializers.ReadOnlyField(
        source="get_most_convincing_rationales"
    )
    peer_impact = serializers.SerializerMethodField()
    urls = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)

    def get_difficulty(self, obj):
        d = obj.get_difficulty()
        return {"score": d[0], "label": d[1], "value": d[2]}

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

    def get_peer_impact(self, obj):
        pi = obj.get_peer_impact()
        return {"score": pi[0], "label": pi[1], "value": pi[2]}

    def get_urls(self, obj):
        urls = {
            "addable_assignments": reverse(
                "REST:teacher-assignment-for-question", args=(obj.pk,)
            ),
            "copy": reverse("teacher:question-copy", args=(obj.pk,)),
            "fix": reverse(
                "question-fix", args=(obj.pk,)
            ),  # TODO: Is this still needed?
            "rationales": reverse("REST:question-rationales", args=(obj.pk,)),
            "test": reverse("question-test", args=(obj.pk,)),
            "update": reverse("teacher:question-update", args=(obj.pk,)),
        }
        if obj.type == "PI":
            urls.update(
                add_answer_choices=reverse(
                    "answer-choice-form", args=(obj.pk,)
                ),
                add_expert_rationales=reverse(
                    "research-fix-expert-rationale", args=(obj.pk,)
                ),
                add_sample_answers=reverse(
                    "sample-answer-form", args=(obj.pk,)
                ),
                matrix=reverse("REST:question-matrix", args=(obj.pk,)),
            )

        return urls

    def validate_image(self, value):
        ALLOWED_IMAGE_FORMATS = ["PNG", "GIF", "JPEG"]
        if value:
            ALLOWED_IMAGE_SIZE = 1e6

            with Image.open(value, formats=ALLOWED_IMAGE_FORMATS) as image:
                image.load()

                if image.format not in ALLOWED_IMAGE_FORMATS:
                    raise serializers.ValidationError(
                        "Invalid image file format.  Allowed formats are "
                        + ", ".join(ALLOWED_IMAGE_FORMATS)
                        + "."
                    )

                if value.size > ALLOWED_IMAGE_SIZE:
                    raise serializers.ValidationError(
                        f"Invalid image file size.  Max: {ALLOWED_IMAGE_SIZE/1e6} MB"  # noqa E501
                    )
        return value

    def validate_text(self, value):
        """Check stripped text length <= 8000."""
        text = bleach.clean(value, tags=[], strip=True).strip()
        if len(text) > 8000:
            raise serializers.ValidationError(_("Text too long"))
        return value

    def validate(self, data):
        """
        - Validation logic is often included in Model.clean(), but DRF ignores.

        - See discussion here https://github.com/encode/django-rest-framework/discussions/7850
        - For now, we reproduce logic in serializer explicitly
        - TODO: Consider how updates in Django admin should be handled since
          serializer validation won't be run.
        """
        # Can't have image without image_alt_text; they must always be changed together  # noqa E501
        if (
            "image" in data
            and data["image"]
            and ("image_alt_text" not in data or not data["image_alt_text"])
        ):
            raise serializers.ValidationError(
                _(
                    "An alternative text for accessibility if is required if providing an image"  # noqa E501
                )
            )
        # Can't have image and video_url
        # - raise validation error if sent together
        # - raise validation error if one sent with other existing on instance
        if (
            "image" in data
            and "video_url" in data
            and data["image"]
            and data["video_url"]
        ):
            raise serializers.ValidationError(
                _(
                    "Only one of the image and video URL fields can be specified"  # noqa E501
                )
            )
        if self.instance and (
            (self.instance.video_url and "image" in data and data["image"])
            or (
                self.instance.image
                and "video_url" in data
                and data["video_url"]
            )
        ):
            raise serializers.ValidationError(
                _(
                    "Only one of the image and video URL fields can be specified"  # noqa E501
                )
            )
        # Only validate answerchoice_set if question type is PI,
        # otherwise ensure empty
        if self.instance:
            if ("type" in data and data["type"] == "PI") or (
                "type" not in data and self.instance.type == "PI"
            ):
                # Update logic - PI
                if self.instance.answerchoice_set.count() < 2 and (
                    "answerchoice_set" not in data
                    or len(data["answerchoice_set"]) < 2
                ):
                    raise serializers.ValidationError(
                        {
                            "answerchoice_set": _(
                                "At least two answer choices are required"
                            )
                        }
                    )
            else:
                # Update logic - RO
                data["answerchoice_set"] = []

        elif "type" not in data or data["type"] == "PI":
            # Create logic - PI
            """
            Check at least two answer choices
            """
            if (
                "answerchoice_set" not in data
                or len(data["answerchoice_set"]) < 2
            ):
                raise serializers.ValidationError(
                    {
                        "answerchoice_set": _(
                            "At least two answer choices are required"
                        )
                    }
                )

            """
            Check at least one answer choice is marked correct
            """
            if sum(x["correct"] for x in data["answerchoice_set"]) == 0:
                raise serializers.ValidationError(
                    {
                        "answerchoice_set": _(
                            "At least one answer choice must be correct"
                        )
                    }
                )
        else:
            # Create logic - RO
            data["answerchoice_set"] = []
        return data

    def create(self, validated_data):
        answerchoice_data = validated_data.pop("answerchoice_set")

        """Create question and attach user"""
        question = super().create(validated_data)
        question.user = self.context["request"].user

        """Create answer choices, sample answers and expert rationales"""
        for i, data in enumerate(answerchoice_data, 1):
            sample_answers = data.pop("sample_answers")

            expert_answers = (
                data.pop("expert_answers") if "expert_answers" in data else []
            )

            # By definition, pk cannot be passed on create
            if "pk" in data:
                data.pop("pk")

            AnswerChoice.objects.create(question=question, **data)
            for sample_answer in sample_answers:
                Answer.objects.create(
                    expert=False,
                    first_answer_choice=i,
                    question=question,
                    rationale=sample_answer["rationale"],
                )
            for expert_answer in expert_answers:
                Answer.objects.create(
                    expert=True,
                    first_answer_choice=i,
                    question=question,
                    rationale=expert_answer["rationale"],
                )

        question.save()

        return question

    def update(self, question, validated_data):
        """
        If answerchoice_set is present:
        - If pk is provided, instance will be updated
        - If pk is missing, instance will be created
        - If existing answerchoice is missing, it will be deleted with related models
        - Same logic for sample and expert answers
        """
        answerchoice_data = None
        if "answerchoice_set" in validated_data:
            answerchoice_data = validated_data.pop("answerchoice_set")

        # Only owner can modify list of collaborators
        if "collaborators_pk" in validated_data:
            collaborators_pk = validated_data.pop("collaborators_pk")

            if question.user == self.request.user:
                question.collaborators.set(collaborators_pk)

        # Update remaining question fields
        for field in validated_data:
            if isinstance(validated_data[field], (list, tuple)):
                _field = getattr(question, field)
                _field.set(validated_data[field])
            else:
                setattr(question, field, validated_data[field])

        question.save()

        if answerchoice_data:
            existing_answerchoices = set(
                question.answerchoice_set.values_list("pk", flat=True)
            )
            # Update/create answer choices
            for i, data in enumerate(answerchoice_data, 1):
                sample_answers = data.pop("sample_answers")

                expert_answers = (
                    data.pop("expert_answers")
                    if "expert_answers" in data
                    else []
                )

                if "pk" in data:
                    # Update answer choice and related models
                    ac = question.answerchoice_set.get(pk=data["pk"])
                    ac.correct = data["correct"]
                    ac.text = data["text"]
                    ac.save()

                    # Sample answers
                    existing = set(
                        ac.sample_answers.values_list("pk", flat=True)
                    )
                    to_update = []
                    to_create = []
                    for sample_answer in sample_answers:
                        if "pk" not in sample_answer:
                            to_create.append(sample_answer)
                        elif sample_answer["pk"] in existing:
                            to_update.append(sample_answer)

                    to_delete = existing - {s["pk"] for s in to_update}

                    for sample_answer in to_update:
                        s = Answer.objects.get(pk=sample_answer["pk"])
                        s.rationale = sample_answer["rationale"]
                        s.save()

                    for sample_answer in to_create:
                        Answer.objects.create(
                            expert=False,
                            first_answer_choice=i,
                            question=question,
                            rationale=sample_answer["rationale"],
                        )

                    for pk in to_delete:
                        s = Answer.objects.get(pk=pk)
                        s.delete()

                    # Expert answers
                    existing = set(
                        ac.expert_answers.values_list("pk", flat=True)
                    )
                    to_update = []
                    to_create = []
                    for expert_answer in expert_answers:
                        if "pk" not in expert_answer:
                            to_create.append(expert_answer)
                        elif expert_answer["pk"] in existing:
                            to_update.append(expert_answer)

                    to_delete = existing - {e["pk"] for e in to_update}

                    for expert_answer in to_update:
                        e = Answer.objects.get(pk=expert_answer["pk"])
                        e.rationale = expert_answer["rationale"]
                        e.save()

                    for expert_answer in to_create:
                        Answer.objects.create(
                            expert=True,
                            first_answer_choice=i,
                            question=question,
                            rationale=expert_answer["rationale"],
                        )

                    if to_create or len(existing) > len(to_delete):
                        for pk in to_delete:
                            e = Answer.objects.get(pk=pk)
                            e.delete()

                else:
                    # Create answer choice and related models
                    AnswerChoice.objects.create(question=question, **data)
                    for sample_answer in sample_answers:
                        Answer.objects.create(
                            expert=False,
                            first_answer_choice=i,
                            question=question,
                            rationale=sample_answer["rationale"],
                        )
                    for expert_answer in expert_answers:
                        Answer.objects.create(
                            expert=True,
                            first_answer_choice=i,
                            question=question,
                            rationale=expert_answer["rationale"],
                        )

            # Delete answer choices
            for pk in existing_answerchoices - {
                ac["pk"]
                if "pk" in ac and ac["pk"] in existing_answerchoices
                else None
                for ac in answerchoice_data
            }:
                ac = question.answerchoice_set.get(pk=pk)
                for sample_answer in ac.sample_answers.all():
                    sample_answer.delete()
                for expert_answer in ac.expert_answers.all():
                    expert_answer.delete()
                ac.delete()

        return question

    def to_representation(self, instance):
        """Bleach on the way out."""
        ret = super().to_representation(instance)
        if "title" in ret:
            ret["title"] = bleach.clean(
                ret["title"], tags=ALLOWED_TAGS, strip=True
            ).strip()
        if "text" in ret:
            ret["text"] = bleach.clean(
                ret["text"], tags=ALLOWED_TAGS, strip=True
            ).strip()

        """Add answer_choice labels"""
        if "answerchoice_set" in ret and ret["answerchoice_set"]:
            for i, ac in enumerate(ret["answerchoice_set"], 1):
                ac.update(label=instance.get_choice_label(i))
        return ret

    class Meta:
        model = Question
        fields = [
            "answer_count",
            "answerchoice_set",
            "answer_style",
            "assignment_count",
            "category",
            "category_pk",
            "collaborators",
            "collaborators_pk",
            "difficulty",
            "discipline",
            "discipline_pk",
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
            "rationale_selection_algorithm",
            "parent",
            "pk",
            "text",
            "title",
            "type",
            "urls",
            "user",
            "video_url",
        ]


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
            "is_valid",  # Added for new assignment interface
            "matrix",
            "peer_impact",  # Added for new assignment interface
            "pk",
            "text",
            "title",
            "type",
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
            assignment.is_editable
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
    is_editable = serializers.ReadOnlyField()
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
            "copy": reverse("REST:teacher-assignment-copy", args=(obj.pk,)),
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
        # TODO: Add check here that user is teacher?
        assignment = super().create(validated_data)

        # TODO: Check that context has request, otherwise raise error or skip
        assignment.owner.add(self.context["request"].user)
        self.context["request"].user.teacher.assignments.add(assignment)
        return assignment

    def update(self, instance, validated_data):
        """
        Only used to reorder questions and change meta data.
        Adding/deleting questions is handled by serializer for through table.
        """
        if "assignmentquestions_set" in validated_data:
            if instance.is_editable:
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
        """Bleach on the way out."""
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
        """Bleach on the way in."""
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
            "intro_page",
            "is_editable",
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
        max_length=1000, required=False
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
        """Check assignment is valid."""
        if not assignment.is_valid:
            logger.error(
                f"Assignment {assignment} is not valid and cannot be distributed."
            )
            raise serializers.ValidationError("Assignment is not valid.")
        return assignment

    def validate_due_date(self, due_date):
        """Check due_date is in the future."""
        if due_date < timezone.now():
            logger.error(f"Invalid due_date: {due_date}")
            raise serializers.ValidationError(
                "Invalid due date (in the past)."
            )
        return due_date

    def validate_group_pk(self, student_group):
        """
        Check that teacher owns group and that group is "assignable".

        - See Teacher model
        """
        if "request" not in self.context:
            logger.error(
                f"Cannot validate student group outside of a request: {student_group}"  # noqa
            )
            raise serializers.ValidationError(
                "Cannot validate student group outside of a request."
            )

        teacher = self.context["request"].user.teacher

        if (
            teacher
            and teacher in student_group.teacher.all()
            and student_group in teacher.assignable_groups.all()
        ):
            return student_group

        logger.error(f"Invalid student group: {student_group}")
        raise serializers.ValidationError("Invalid student group.")

    def validate(self, data):
        """Check unique_together constraint on assignment and group."""
        assignment = (
            data["assignment"]
            if "assignment" in data
            else self.instance.assignment
        )
        group = data["group"] if "group" in data else self.instance.group
        queryset = StudentGroupAssignment.objects.filter(
            assignment=assignment, group=group
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            logger.error(
                f"Assignment {assignment} already distributed to {group}."
            )
            raise serializers.ValidationError(
                f"Assignment already distributed to {group}."
            )

        """Check order."""
        if "order" in data:
            if self.instance:
                if err := self.instance._verify_order(data["order"]):
                    logger.error(err)
                    raise serializers.ValidationError(err)
            elif err := StudentGroupAssignment.verify_order(
                data["order"], data["assignment"].questions.count()
            ):
                raise serializers.ValidationError(err)

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
