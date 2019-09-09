# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import itertools
import string
from datetime import datetime

import pytz
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.encoding import smart_bytes
from django.utils.html import escape, strip_tags
from django.utils.translation import ugettext_lazy as _

from reputation.models import Reputation

from .. import rationale_choice
from .search import MetaSearch


def no_hyphens(value):
    if "-" in value:
        raise ValidationError(_("Hyphens may not be used in this field."))


def images(instance, filename):
    hash = hashlib.sha256(
        "{}-{}".format(datetime.now(), smart_bytes(filename))
    ).hexdigest()[:8]
    path = "images/{0}/{1}/{2}_{3}".format(
        instance.user.username, datetime.now().month, hash, filename
    )
    return path


class Category(models.Model):
    title = models.CharField(
        _("Category Name"),
        unique=True,
        max_length=100,
        help_text=_("Enter the name of a new question category."),
        validators=[no_hyphens],
    )

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")


class Discipline(models.Model):
    title = models.CharField(
        _("Discipline name"),
        unique=True,
        max_length=100,
        help_text=_("Enter the name of a new discipline."),
        validators=[no_hyphens],
    )

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("discipline")
        verbose_name_plural = _("disciplines")


class GradingScheme(object):
    STANDARD = 0
    ADVANCED = 1


QUESTION_TYPES = (("PI", "Peer instruction"), ("RO", "Rationale only"))


class QuestionManager(models.Manager):
    def get_by_natural_key(self, title):
        return self.get(title=title)


class QuestionFlag(models.Model):
    question = models.ForeignKey("Question")
    flag_reason = models.ManyToManyField("QuestionFlagReason")
    user = models.ForeignKey(User)
    flag = models.BooleanField(default=True)
    comment = models.CharField(max_length=200, null=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
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

        return (
            super(FlaggedQuestionManager, self)
            .get_queryset()
            .filter(pk__in=flagged_questions)
        )


class UnflaggedQuestionManager(models.Manager):
    def get_queryset(self):
        flagged_questions = QuestionFlag.objects.filter(flag=True).values_list(
            "question", flat=True
        )

        return (
            super(UnflaggedQuestionManager, self)
            .get_queryset()
            .exclude(pk__in=flagged_questions)
        )


class Question(models.Model):
    objects = QuestionManager()
    flagged_objects = FlaggedQuestionManager()
    unflagged_objects = UnflaggedQuestionManager()

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
            "Optional. A video to include after the question text. All "
            "videos should include transcripts.  Format: "
            "https://www.youtube.com/embed/..."
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

    def __unicode__(self):
        if self.discipline:
            return "{} - {}".format(self.discipline, self.title)
        return self.title

    def get_start_form_class(self):
        from ..forms import FirstAnswerForm

        return FirstAnswerForm

    def start_form_valid(request, view, form):
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
            errors.update({f: msg for f in fields})
        if self.image and not self.image_alt_text:
            msg = _(
                "You must provide alternative text for accessibility if "
                "providing an image."
            )
            errors.update({"image_alt_text": msg})
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
            return itertools.imap(str, itertools.count(1))
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

    def get_matrix(self):
        matrix = {}
        matrix[str("easy")] = 0
        matrix[str("hard")] = 0
        matrix[str("tricky")] = 0
        matrix[str("peer")] = 0

        answer_choices = self.answerchoice_set.all()
        answerchoice_correct = self.answerchoice_set.values_list(
            "correct", flat=True
        )
        correct_choices = list(
            itertools.compress(itertools.count(1), answerchoice_correct)
        )

        # There must be more choices than correct choices for valid matrix
        if answer_choices.count() > len(correct_choices):
            student_answers = (
                self.answer_set.filter(expert=False)
                .filter(second_answer_choice__gt=0)
                .exclude(user_token="")
            )
            N = len(student_answers)
            if N > 0:

                easy = (
                    student_answers.filter(
                        first_answer_choice__in=correct_choices
                    )
                    .filter(second_answer_choice__in=correct_choices)
                    .count()
                )

                hard = (
                    student_answers.exclude(
                        first_answer_choice__in=correct_choices
                    )
                    .exclude(second_answer_choice__in=correct_choices)
                    .count()
                )

                tricky = (
                    student_answers.filter(
                        first_answer_choice__in=correct_choices
                    )
                    .exclude(second_answer_choice__in=correct_choices)
                    .count()
                )

                # peer = (
                #     student_answers.exclude(
                #         first_answer_choice__in=correct_choices
                #     )
                #     .filter(second_answer_choice__in=correct_choices)
                #     .count()
                # )

                # assert easy + hard + tricky + peer == N

                peer = N - easy - tricky - hard

                matrix[str("easy")] = float(easy) / N
                matrix[str("hard")] = float(hard) / N
                matrix[str("tricky")] = float(tricky) / N
                matrix[str("peer")] = float(peer) / N

        return matrix

    def get_frequency(self, all_rationales=False):
        choice1 = {}
        choice2 = {}
        frequency = {}
        if all_rationales:
            # all rationales, including those enetered as samples by teachers
            student_answers = self.answer_set.filter(first_answer_choice__gt=0)
        else:
            # only rationales enetered by students
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
            choice1[smart_bytes(label)] = student_answers.filter(
                first_answer_choice=c
            ).count()
            choice2[smart_bytes(label)] = student_answers.filter(
                second_answer_choice=c
            ).count()
            c = c + 1

        frequency[str("first_choice")] = choice1
        frequency[str("second_choice")] = choice2

        return frequency

    def get_frequency_json(self, choice_index_name):
        frequency_dict = self.get_frequency(all_rationales=True)[
            choice_index_name
        ]
        return [
            {"answer_label": key, "frequency": value}
            for key, value in frequency_dict.items()
        ]

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")


class QuestionFlagReason(models.Model):
    title = models.CharField(
        _("Reason for flagging a question"),
        unique=True,
        max_length=100,
        help_text=_("Reason for flagging a question."),
        validators=[no_hyphens],
    )

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("Question flag reason")
