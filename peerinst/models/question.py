import hashlib
import itertools
import string
from datetime import datetime

import bleach
import pandas as pd
import pytz
from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core import exceptions
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.utils.html import escape, strip_tags
from django.utils.translation import gettext_lazy as _

from peerinst import rationale_choice
from peerinst.grammar import basic_syntax
from peerinst.templatetags.bleach_html import ALLOWED_TAGS
from reputation.models import Reputation

from .search import MetaSearch


def no_hyphens(value):
    if "-" in value:
        raise ValidationError(_("Hyphens may not be used in this field."))


def images(instance, filename):
    hash = hashlib.sha256(f"{datetime.now()}-{filename}".encode()).hexdigest()[
        :8
    ]
    return (
        f"images/{instance.user.username}/{datetime.now().month}/{hash}_{filename}"
        if instance.user
        else f"images/unknown/{datetime.now().month}/{hash}_{filename}"
    )


class Category(models.Model):
    title = models.CharField(
        _("Category"),
        unique=True,
        max_length=100,
        help_text=_("Enter the title of the question category."),
        validators=[no_hyphens],
    )

    def save(self, *args, **kwargs):
        """Bleach"""
        self.title = bleach.clean(
            self.title,
            tags=[],
            strip=True,
        ).strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("title",)
        verbose_name = _("category")
        verbose_name_plural = _("categories")


class Subject(models.Model):
    title = models.CharField(
        _("Subject"),
        unique=True,
        max_length=100,
        help_text=_("Enter the title of the subject."),
        validators=[no_hyphens],
    )
    discipline = models.ForeignKey(
        "Discipline", blank=True, null=True, on_delete=models.SET_NULL
    )
    categories = models.ManyToManyField(
        Category, related_name="subjects", blank=True
    )

    def save(self, *args, **kwargs):
        """Bleach"""
        self.title = bleach.clean(
            self.title,
            tags=[],
            strip=True,
        ).strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("title",)
        verbose_name = _("subject")
        verbose_name_plural = _("subjects")


class Discipline(models.Model):
    title = models.CharField(
        _("Discipline"),
        unique=True,
        max_length=100,
        help_text=_("Enter the title of the discipline."),
        validators=[no_hyphens],
    )

    def save(self, *args, **kwargs):
        """Bleach"""
        self.title = bleach.clean(
            self.title,
            tags=[],
            strip=True,
        ).strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("title",)
        verbose_name = _("discipline")
        verbose_name_plural = _("disciplines")


class GradingScheme:
    STANDARD = 0
    ADVANCED = 1


QUESTION_TYPES = (("PI", "Peer instruction"), ("RO", "Rationale only"))


class QuestionManager(models.Manager):
    def get_by_natural_key(self, title):
        return self.get(title=title)


class QuestionFlag(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    flag_reason = models.ManyToManyField("QuestionFlagReason")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flag = models.BooleanField(default=True)
    comment = models.CharField(max_length=200, null=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}- {}- {}".format(
            self.question.pk, self.question, self.user.email, self.comment
        )

    class Meta:
        verbose_name = _("flagged question")


class FlaggedQuestionManager(models.Manager):
    def get_queryset(self):
        flagged_questions = QuestionFlag.objects.filter(flag=True).values_list(
            "question", flat=True
        )

        return super().get_queryset().filter(pk__in=flagged_questions)


class UnflaggedQuestionManager(models.Manager):
    def get_queryset(self):
        flagged_questions = QuestionFlag.objects.filter(flag=True).values_list(
            "question", flat=True
        )

        return super().get_queryset().exclude(pk__in=flagged_questions)


class Question(models.Model):
    objects = QuestionManager()
    flagged_objects = FlaggedQuestionManager()
    unflagged_objects = UnflaggedQuestionManager()

    DIFFICULTY_LABELS = (
        (1, _("Easy")),
        (2, _("Avg")),
        (3, _("Hard")),
        (4, _("Not enough data")),
    )

    PEER_IMPACT_LABELS = (
        (1, _("Low")),
        (2, _("Med")),
        (3, _("High")),
        (4, _("Not enough data")),
    )

    id = models.AutoField(
        primary_key=True,
        help_text=_(
            "Use this ID to refer to the question in the LMS. Note: The "
            "question will have to have been saved at least once before an ID "
            "is available."
        ),
    )
    type = models.CharField(
        _("Question type"),
        max_length=2,
        choices=QUESTION_TYPES,
        default="PI",
        help_text=_(
            "Choose 'peer instruction' for two-step multiple choice with "
            "rationale or 'rationale only' for a simple text response."
        ),
    )
    title = models.CharField(
        _("Question title"),
        unique=True,
        max_length=100,
        help_text=_("A title for the question."),
    )
    text = models.TextField(
        _("Question text"), help_text=_("Enter the question text.")
    )
    parent = models.ForeignKey(
        "Question", blank=True, null=True, on_delete=models.SET_NULL
    )
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL
    )

    second_answer_needed = models.BooleanField(default=True, editable=False)

    def teachers_only():
        return Q(teacher__isnull=False)

    collaborators = models.ManyToManyField(
        User,
        blank=True,
        related_name="collaborators",
        help_text=_("Optional. Other users that may also edit this question."),
        limit_choices_to=teachers_only(),
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    image = models.ImageField(
        _("Question image"),
        blank=True,
        null=True,
        upload_to=images,
        help_text=_(
            "Optional. An image to include after the question text. Accepted "
            "formats: .jpg, .jpeg, .png, .gif"
        ),
    )
    image_alt_text = models.CharField(
        _("Image Alt Text"),
        blank=True,
        max_length=1024,
        help_text=_(
            "Optional. Alternative text for accessibility. For instance, the "
            "student may be using a screen reader."
        ),
    )
    # Videos will be handled by off-site services.
    video_url = models.URLField(
        _("Question video URL"),
        blank=True,
        help_text=_(
            "Optional. A video or simulation to include after the question "
            "text. All videos should include transcripts.  Only videos from "
            "youtube (i.e. https://www.youtube.com/embed/...) and simulations "
            "from phet (i.e. https://phet.colorado.edu/sims/html/...) are "
            "currently supported."
        ),
    )
    ALPHA = 0
    NUMERIC = 1
    ANSWER_STYLE_CHOICES = ((ALPHA, "alphabetic"), (NUMERIC, "numeric"))
    answer_style = models.IntegerField(
        _("Answer style"),
        choices=ANSWER_STYLE_CHOICES,
        default=ALPHA,
        help_text=_(
            "Whether the answers are annotated with letters (A, B, C…) or "
            "numbers (1, 2, 3…)."
        ),
    )
    category = models.ManyToManyField(
        Category,
        _("Categories"),
        help_text=_(
            "Type to search and select at least one category for this "
            "question. You can select multiple categories."
        ),
    )
    discipline = models.ForeignKey(
        Discipline,
        blank=True,
        null=True,
        help_text=_(
            "Optional. Select the discipline to which this item should "
            "be associated."
        ),
        on_delete=models.SET_NULL,
    )
    fake_attributions = models.BooleanField(
        _("Add fake attributions"),
        default=False,
        help_text=_(
            "Add random fake attributions consisting of username and country "
            "to rationales. "
        ),
    )
    sequential_review = models.BooleanField(
        _("Sequential rationale review"),
        default=False,
        help_text=_(
            "Show rationales sequentially and allow to vote on them before "
            "the final review."
        ),
    )
    rationale_selection_algorithm = models.CharField(
        _("Rationale selection algorithm"),
        choices=rationale_choice.algorithm_choices(),
        default="prefer_expert_and_highly_voted",
        max_length=100,
        help_text=_(
            "The algorithm to use for choosing the rationales presented to "
            "students during question review.  This option is ignored if you "
            "selected sequential review."
        ),
    )
    GRADING_SCHEME_CHOICES = (
        (GradingScheme.STANDARD, _("Standard")),
        (GradingScheme.ADVANCED, _("Advanced")),
    )
    grading_scheme = models.IntegerField(
        _("Grading scheme"),
        choices=GRADING_SCHEME_CHOICES,
        default=GradingScheme.STANDARD,
        help_text=_(
            "Grading scheme to use. "
            'The "Standard" scheme awards 1 point if the student\'s final '
            'answer is correct, and 0 points otherwise. The "Advanced" scheme '
            "awards 0.5 points if the student's initial guess is correct, and "
            "0.5 points if they subsequently stick with or change to the "
            "correct answer."
        ),
    )
    reputation = models.OneToOneField(
        Reputation, blank=True, null=True, on_delete=models.SET_NULL
    )
    meta_search = GenericRelation(MetaSearch, related_query_name="questions")

    def __str__(self):
        if self.discipline:
            return f"{self.discipline} - {self.title}"
        return self.title

    def save(self, *args, **kwargs):
        """Bleach"""
        self.text = bleach.clean(
            self.text,
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()
        self.title = bleach.clean(
            self.title,
            tags=ALLOWED_TAGS,
            strip=True,
        ).strip()

        if self.type == "PI":
            self.second_answer_needed = True

        elif self.type == "RO":
            self.second_answer_needed = False

        super().save(*args, **kwargs)

    @classmethod
    def deleted_questions(cls):
        """
        Exclude questions which are part of any Teacher's deleted_questions,
        and have no answers
        """
        Teacher = apps.get_model(app_label="peerinst", model_name="teacher")

        return cache.get_or_set(
            "deleted_questions",
            cls.objects.filter(
                pk__in=set(
                    Teacher.objects.all()
                    .prefetch_related("deleted_questions__question")
                    .values_list("deleted_questions__question", flat=True)
                ).intersection(
                    set(
                        cls.objects.all()
                        .annotate(answer_count=Count("answer"))
                        .filter(answer_count=0)
                        .values_list("id", flat=True)
                    )
                )
            ),
            60,
        )

    @classmethod
    def is_missing_answer_choices(cls, queryset):
        if not isinstance(queryset, models.query.EmptyQuerySet):
            if isinstance(queryset, models.query.QuerySet):
                if queryset.model is cls:
                    return (
                        queryset.filter(type="PI")
                        .annotate(answer_choice_count=Count("answerchoice"))
                        .annotate(
                            correct_answer_choice_count=Count(
                                "answerchoice",
                                filter=Q(answerchoice__correct=True),
                            )
                        )
                        .filter(
                            Q(answer_choice_count__lte=1)
                            | Q(correct_answer_choice_count=0)
                        )
                        .exists()
                    )
                raise TypeError("Queryset must be of type Question")
            else:
                raise TypeError(
                    f"Method only implemented for querysets.  Passed {type(queryset)}"  # noqa E501
                )
        return False

    @classmethod
    def is_missing_expert_rationale(cls, queryset):
        if not isinstance(queryset, models.query.EmptyQuerySet):
            if isinstance(queryset, models.query.QuerySet):
                if queryset.model is cls:
                    Answer = apps.get_model(
                        app_label="peerinst", model_name="answer"
                    )
                    expert_answers = Answer.objects.filter(expert=True).filter(
                        question=OuterRef("pk")
                    )

                    return (
                        queryset.filter(type="PI")
                        .values("answerchoice", "answerchoice__correct")
                        .annotate(
                            rank=Subquery(
                                cls.objects.filter(pk=OuterRef("pk"))
                                .values("answerchoice")
                                .filter(
                                    answerchoice__lte=OuterRef("answerchoice")
                                )
                                .annotate(count=Count("answerchoice"))
                                .values("count")[:1],
                                output_field=models.IntegerField(),
                            ),
                        )
                        .annotate(correct=F("answerchoice__correct"))
                        .annotate(
                            expert_answers_for_choice=Subquery(
                                expert_answers.filter(
                                    first_answer_choice=OuterRef("rank")
                                )
                                .values("pk")
                                .annotate(count=Count("pk"))
                                .values("count")[:1],
                                output_field=models.IntegerField(),
                            )
                        )
                        .filter(
                            Q(correct=True)
                            & Q(expert_answers_for_choice__isnull=True)
                        )
                        .exists()
                    )
                raise TypeError("Queryset must be of type Question")
            else:
                raise TypeError(
                    f"Method only implemented for querysets.  Passed {type(queryset)}"  # noqa E501
                )
        return False

    @classmethod
    def is_missing_sample_answers(cls, queryset):
        if not isinstance(queryset, models.query.EmptyQuerySet):
            if isinstance(queryset, models.query.QuerySet):
                if queryset.model is cls:
                    Answer = apps.get_model(
                        app_label="peerinst", model_name="answer"
                    )
                    sample_answers = Answer.objects.filter(
                        expert=False
                    ).filter(question=OuterRef("pk"))

                    return (
                        queryset.filter(type="PI")
                        .values("answerchoice")
                        .annotate(
                            rank=Subquery(
                                cls.objects.filter(pk=OuterRef("pk"))
                                .values("answerchoice")
                                .filter(
                                    answerchoice__lte=OuterRef("answerchoice")
                                )
                                .annotate(count=Count("answerchoice"))
                                .values("count")[:1],
                                output_field=models.IntegerField(),
                            ),
                        )
                        .annotate(
                            sample_answers_for_choice=Subquery(
                                sample_answers.filter(
                                    first_answer_choice=OuterRef("rank")
                                )
                                .values("pk")
                                .annotate(count=Count("pk"))
                                .values("count")[:1],
                                output_field=models.IntegerField(),
                            )
                        )
                        .filter(sample_answers_for_choice__isnull=True)
                        .exists()
                    )
                raise TypeError("Queryset must be of type Question")
            else:
                raise TypeError(
                    f"Method only implemented for querysets.  Passed {type(queryset)}"  # noqa E501
                )
        return False

    @classmethod
    def is_flagged(cls, queryset):
        if not isinstance(queryset, models.query.EmptyQuerySet):
            if isinstance(queryset, models.query.QuerySet):
                if queryset.model is cls:
                    return (
                        queryset.annotate(
                            flagged=Count(
                                "questionflag",
                                filter=Q(questionflag__flag=True),
                            )
                        )
                        .filter(flagged__gt=0)
                        .exists()
                    )
                raise TypeError("Queryset must be of type Question")
            else:
                raise TypeError(
                    f"Method only implemented for querysets.  Passed {type(queryset)}"  # noqa E501
                )
        return False

    @property
    def answer_count(self):
        return self.get_student_answers().count()

    @property
    def assignment_count(self):
        return self.assignment_set.all().count()

    @property
    def collections(self):
        Collection = apps.get_model(
            app_label="peerinst", model_name="collection"
        )
        return Collection.objects.filter(assignments__questions=self)

    @property
    def featured(self):
        Collection = apps.get_model(
            app_label="peerinst", model_name="collection"
        )
        return self.id in Collection.featured_questions()

    @property
    def is_editable(self):
        return (
            self.answer_set.filter(expert=False)
            .exclude(user_token__exact="")
            .count()
            == 0
        )

    @property
    def is_not_flagged(self):
        self_as_queryset = Question.objects.filter(pk=self.pk)
        return not Question.is_flagged(self_as_queryset)

    @property
    def is_not_missing_answer_choices(self):
        self_as_queryset = Question.objects.filter(pk=self.pk)
        return not Question.is_missing_answer_choices(self_as_queryset)

    @property
    def is_not_missing_expert_rationale(self):
        self_as_queryset = Question.objects.filter(pk=self.pk)
        return not Question.is_missing_expert_rationale(self_as_queryset)

    @property
    def is_not_missing_sample_answers(self):
        self_as_queryset = Question.objects.filter(pk=self.pk)
        return not Question.is_missing_sample_answers(self_as_queryset)

    @property
    def is_valid(self):
        self_as_queryset = Question.objects.filter(pk=self.pk)
        return not any(
            [
                Question.is_missing_answer_choices(self_as_queryset),
                Question.is_missing_expert_rationale(self_as_queryset),
                Question.is_missing_sample_answers(self_as_queryset),
                Question.is_flagged(self_as_queryset),
            ]
        )

    @property
    def flag_reasons(self):
        return (
            QuestionFlag.objects.filter(question=self, flag=True)
            .values("flag_reason__title")
            .annotate(Count("flag_reason"))
        )

    def get_start_form_class(self):
        from peerinst.forms import FirstAnswerForm

        return FirstAnswerForm

    def start_form_valid(self, view, form):
        first_answer_choice = int(form.cleaned_data["first_answer_choice"])
        correct = view.question.is_correct(first_answer_choice)
        rationale = form.cleaned_data["rationale"]
        datetime_first = datetime.now(pytz.utc).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        view.stage_data.update(
            first_answer_choice=first_answer_choice,
            rationale=rationale,
            datetime_first=datetime_first,
            completed_stage="start",
        )
        view.emit_event(
            "problem_check",
            first_answer_choice=first_answer_choice,
            success="correct" if correct else "incorrect",
            rationale=rationale,
        )
        return

    def clean(self):
        errors = {}
        fields = ["image", "video_url"]
        filled_in_fields = sum(bool(getattr(self, f)) for f in fields)
        if filled_in_fields > 1:
            msg = _(
                "You can only specify one of the image and video URL fields."
            )
            errors |= {f: msg for f in fields}
        if self.image and not self.image_alt_text:
            msg = _(
                "You must provide alternative text for accessibility if "
                "providing an image."
            )
            errors["image_alt_text"] = msg
        if errors:
            raise exceptions.ValidationError(errors)

    def natural_key(self):
        return (self.title,)

    def get_choice_label_iter(self):
        """
        Return an iterator over the answer labels with the style determined
        by answer_style.
        The iterable doesn't stop after the current number of answer choices.
        """
        if self.answer_style == Question.ALPHA:
            return iter(string.ascii_uppercase)
        elif self.answer_style == Question.NUMERIC:
            return map(str, itertools.count(1))
        raise ValueError(
            "The field Question.answer_style has an invalid value."
        )

    def get_choice_label(self, index):
        """
        Return an answer label for answer index with the style determined by
        answer_style.
        This method does not check whether index is out of bounds.
        """
        if index is None:
            return None
        elif self.answer_style == Question.ALPHA:
            return string.ascii_uppercase[index - 1]
        elif self.answer_style == Question.NUMERIC:
            return str(index)
        raise ValueError(
            "The field Question.answer_style has an invalid value."
        )

    def get_choices(self):
        """Return a list of pairs (answer label, answer choice text)."""
        return [
            (label, choice.text)
            for label, choice in zip(
                self.get_choice_label_iter(), self.answerchoice_set.all()
            )
        ]

    def is_correct(self, index):
        return self.answerchoice_set.all()[index - 1].correct

    def get_correct_choices(self):
        answerchoice_correct = self.answerchoice_set.values_list(
            "correct", flat=True
        )
        return list(
            itertools.compress(itertools.count(1), answerchoice_correct)
        )

    def get_student_answers(self):
        return (
            self.answer_set.filter(expert=False)
            .filter(second_answer_choice__gt=0)
            .exclude(user_token="")
        )

    def get_answers_by_type(self, answer_type):
        """
        Arguments:
        ----------
            answer_type: string, one of following possible choices:
                        - *R (second answer choice correct)
                        - *W (second answer choice wrong)
                        - RR (right to right),
                        - RW (right to wrong),
                        - WR,
                        - WR
        Returns:
        -------
            queryset of student answers

        """
        student_answers = self.get_student_answers()
        correct_choices = self.get_correct_choices()

        if answer_type == "*R":
            qs = student_answers.filter(
                second_answer_choice__in=correct_choices
            )
        if answer_type == "*W":
            qs = student_answers.exclude(
                second_answer_choice__in=correct_choices
            )
        elif answer_type == "RR":
            qs = student_answers.filter(
                first_answer_choice__in=correct_choices
            ).filter(second_answer_choice__in=correct_choices)
        elif answer_type == "RW":
            qs = student_answers.filter(
                first_answer_choice__in=correct_choices
            ).exclude(second_answer_choice__in=correct_choices)
        elif answer_type == "WR":
            qs = student_answers.exclude(
                first_answer_choice__in=correct_choices
            ).filter(second_answer_choice__in=correct_choices)
        elif answer_type == "WW":
            qs = student_answers.exclude(
                first_answer_choice__in=correct_choices
            ).exclude(second_answer_choice__in=correct_choices)

        return qs

    def get_difficulty(self):
        MIN_ANSWERS = 30
        UPPER_BOUND = 0.50
        LOWER_BOUND = 0.25

        N = self.get_student_answers().count()
        if N > MIN_ANSWERS:
            difficulty = self.get_answers_by_type(answer_type="*W").count() / N
            if difficulty >= UPPER_BOUND:
                difficulty_label = self.DIFFICULTY_LABELS[2]
            elif difficulty < LOWER_BOUND:
                difficulty_label = self.DIFFICULTY_LABELS[0]
            else:
                difficulty_label = self.DIFFICULTY_LABELS[1]
        else:
            difficulty = None
            difficulty_label = self.DIFFICULTY_LABELS[3]
        return (difficulty, *difficulty_label)

    def get_peer_impact(self):
        MIN_ANSWERS = 30
        UPPER_BOUND = 0.25
        LOWER_BOUND = 0.05

        N = self.get_student_answers().count()
        if N > MIN_ANSWERS:
            peer_impact = (
                self.get_answers_by_type(answer_type="RW").count()
                + self.get_answers_by_type(answer_type="WR").count()
            ) / N
            if peer_impact >= UPPER_BOUND:
                peer_impact_label = self.PEER_IMPACT_LABELS[2]
            elif peer_impact < LOWER_BOUND:
                peer_impact_label = self.PEER_IMPACT_LABELS[0]
            else:
                peer_impact_label = self.PEER_IMPACT_LABELS[1]
        else:
            peer_impact = None
            peer_impact_label = self.PEER_IMPACT_LABELS[3]
        return (peer_impact, *peer_impact_label)

    def get_matrix(self):
        matrix = {}
        matrix["easy"] = 0
        matrix["hard"] = 0
        matrix["tricky"] = 0
        matrix["peer"] = 0

        answer_choices = self.answerchoice_set.all()
        correct_choices = self.get_correct_choices()

        # There must be more choices than correct choices for valid matrix
        if answer_choices.count() > len(correct_choices):
            student_answers = self.get_student_answers()
            N = len(student_answers)
            if N > 0:
                easy = self.get_answers_by_type(answer_type="RR").count()

                hard = self.get_answers_by_type(answer_type="WW").count()

                tricky = self.get_answers_by_type(answer_type="RW").count()

                # peer = (
                #     student_answers.exclude(
                #         first_answer_choice__in=correct_choices
                #     )
                #     .filter(second_answer_choice__in=correct_choices)
                #     .count()
                # )

                # assert easy + hard + tricky + peer == N

                peer = N - easy - tricky - hard

                matrix["easy"] = float(easy) / N
                matrix["hard"] = float(hard) / N
                matrix["tricky"] = float(tricky) / N
                matrix["peer"] = float(peer) / N

        return matrix

    def get_frequency(self, all_rationales=False):
        choice1 = {}
        choice2 = {}
        frequency = {}
        if all_rationales:
            # all rationales, including those entered as samples by teachers,
            # but exclude expert rationales, since they are no longer shown
            # to students on review step
            student_answers = self.answer_set.filter(
                first_answer_choice__gt=0
            ).exclude(expert=True)
        else:
            # only rationales entered by students
            student_answers = (
                self.answer_set.filter(expert=False)
                .filter(first_answer_choice__gt=0)
                .filter(second_answer_choice__gt=0)
            )
        c = 1
        for answerChoice in self.answerchoice_set.all():
            label = (
                self.get_choice_label(c)
                + ". "
                + escape(strip_tags(answerChoice.text)).replace(
                    "&amp;nbsp;", " "
                )
            )
            if len(label) > 50:
                label = label[0:50] + "..."
            choice1[label] = student_answers.filter(
                first_answer_choice=c
            ).count()
            choice2[label] = student_answers.filter(
                second_answer_choice=c
            ).count()
            c = c + 1

        frequency["first_choice"] = choice1
        frequency["second_choice"] = choice2

        return frequency

    def get_frequency_json(self, choice_index_name):
        frequency_dict = self.get_frequency(all_rationales=True)[
            choice_index_name
        ]
        return [
            {"answer_label": key, "frequency": value}
            for key, value in list(frequency_dict.items())
        ]

    def get_vote_data(self):
        """
        Returns:
        --------
        DataFrame with columns:
            index: answer_id
            times_shown -> int
            times_chosen -> int
        """

        from peerinst.models import ShownRationale

        answer_qs = self.answer_set.all()

        df_chosen_ids = pd.DataFrame(
            answer_qs.values(
                "chosen_rationale__id", "question_id", "user_token"
            )
        )

        df_chosen = (
            df_chosen_ids["chosen_rationale__id"]
            .value_counts()
            .to_frame()
            .rename(columns={"count": "times_chosen"})
        )

        df_shown_ids = pd.DataFrame(
            ShownRationale.objects.filter(
                shown_for_answer__in=answer_qs
            ).values("shown_answer__id")
        )

        # ShownRationale data only collected since Jan 2019
        if df_shown_ids.shape[0] > 0:
            df_shown = (
                df_shown_ids["shown_answer__id"]
                .value_counts()
                .to_frame()
                .rename(columns={"count": "times_shown"})
            )

            df_votes = pd.merge(
                df_chosen,
                df_shown,
                left_index=True,
                right_index=True,
                how="right",
            ).sort_values("times_shown", ascending=False)
        else:
            df_votes = df_chosen
            df_votes.loc[:, "times_shown"] = pd.Series(0)

        df_votes = df_votes.fillna(0)

        df_votes = df_votes.astype(int)

        return df_votes

    def get_most_convincing_rationales(self):
        """
        Returns:
        --------
        List[
            {
                "answer" -> str,
                "correct" -> bool,
                "answer_text" -> str,
                "most_convincing":{
                    "times_chosen" -> int,
                    "times_shown" -> int,
                    "rationale" -> str
                }
            }
        ]
        """
        answerchoice_correct = self.answerchoice_set.values_list(
            "correct", flat=True
        )

        q_answerchoices = {
            i: (
                label,
                correct,
                bleach.clean(
                    text,
                    tags=ALLOWED_TAGS,
                    strip=True,
                ).strip(),
            )
            for i, (correct, (label, text)) in enumerate(
                zip(answerchoice_correct, self.get_choices()), start=1
            )
        }

        # there are some places in db where
        # first_answer_choice value is greater than
        # possible number of answer_choices.
        # Remove those answers
        answer_qs = self.answer_set.filter(
            first_answer_choice__lte=self.answerchoice_set.count()
        )

        if answer_qs.count() > 0:
            df_votes = self.get_vote_data()

            df_answers = pd.DataFrame(
                answer_qs.values("id", "first_answer_choice", "rationale")
            )

            df = pd.merge(df_answers, df_votes, left_on="id", right_index=True)

            # TODO: Replace length filter with quality filter
            df_top5 = (
                df.loc[df["rationale"].str.len() >= 10, :]
                .sort_values(
                    ["first_answer_choice", "times_chosen", "times_shown"],
                    ascending=[True, False, False],
                )
                .groupby("first_answer_choice")
                .head(5)
            )

            r = []
            for first_answer_choice, best_answers in df_top5.groupby(
                "first_answer_choice"
            ):
                d = {}
                d["label"] = q_answerchoices[first_answer_choice][0]
                d["text"] = bleach.clean(
                    q_answerchoices[first_answer_choice][2],
                    tags=ALLOWED_TAGS,
                    strip=True,
                )
                d["correct"] = q_answerchoices[first_answer_choice][1]
                most_convincing = best_answers.loc[
                    :, ["id", "times_chosen", "times_shown", "rationale"]
                ]
                most_convincing["rationale"] = most_convincing[
                    "rationale"
                ].apply(
                    lambda x: basic_syntax(
                        bleach.clean(x, tags=[], strip=True)
                    )
                )
                d["most_convincing"] = most_convincing.to_dict(
                    orient="records"
                )
                r.append(d)

        else:
            r = []

        return r

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")


class QuestionFlagReason(models.Model):
    CHOICES = (
        (
            "Clarification needed",
            _("The question, or one of the answer choices, is unclear."),
        ),
        (
            "Potential copyright issues",
            _(
                """
                Some part of the question, perhaps the image or \
                attached video, may come from a copyrighted source.
                """
            ),
        ),
        (
            "Wrong answer marked as correct",
            _(
                """
                Wrong answer marked as correct
                """
            ),
        ),
    )

    title = models.CharField(
        _("Reason for flagging a question"),
        unique=True,
        max_length=100,
        help_text=_("Reason for flagging a question."),
        choices=CHOICES,
        default=CHOICES[0][0],
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Question flag reason")
