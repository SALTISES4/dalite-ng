from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from quality.models import Quality

from .assignment import Assignment, StudentGroupAssignment
from .question import GradingScheme, Question


class AnswerMayShowManager(models.Manager):
    def get_queryset(self):
        never_show = [
            a
            for a in set(
                AnswerAnnotation.objects.filter(score=0).values_list(
                    "answer", flat=True
                )
            )
        ]
        return (
            super(AnswerMayShowManager, self)
            .get_queryset()
            .exclude(pk__in=never_show)
        )


class AnswerChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(_("Text"), max_length=500)
    correct = models.BooleanField(_("Correct?"))

    def __str__(self):
        return self.text

    class Meta:
        ordering = ["id"]
        verbose_name = _("answer choice")
        verbose_name_plural = _("answer choices")


class Answer(models.Model):

    objects = models.Manager()
    may_show = AnswerMayShowManager()

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    assignment = models.ForeignKey(
        Assignment, blank=True, null=True, on_delete=models.CASCADE
    )
    student_group_assignment = models.ForeignKey(
        StudentGroupAssignment, blank=True, null=True, on_delete=models.CASCADE
    )

    first_answer_choice = models.PositiveSmallIntegerField(
        _("First answer choice")
    )
    rationale = models.TextField(_("Rationale"))
    second_answer_choice = models.PositiveSmallIntegerField(
        _("Second answer choice"), blank=True, null=True
    )
    shown_rationales = models.ManyToManyField(
        "self",
        blank=True,
        through="ShownRationale",
        symmetrical=False,
        related_name="shown_rationales_all",
    )
    chosen_rationale = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE
    )
    user_token = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Corresponds to the user's username."),
    )
    show_to_others = models.BooleanField(_("Show to others?"), default=True)
    expert = models.BooleanField(
        _("Expert rationale?"),
        default=False,
        help_text=_("Whether this answer is a pre-seeded expert rationale."),
    )
    datetime_start = models.DateTimeField(blank=True, null=True)
    datetime_first = models.DateTimeField(blank=True, null=True)
    datetime_second = models.DateTimeField(blank=True, null=True)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    checked_by_quality = models.ForeignKey(
        Quality,
        blank=True,
        null=True,
        help_text="Which quality was used to check if rationale is accepted",
        related_name="checking_quality",
        on_delete=models.CASCADE,
    )
    filtered_with_quality = models.ForeignKey(
        Quality,
        blank=True,
        null=True,
        help_text="Which quality was used to filter shown rationales.",
        related_name="filtering_quality",
        on_delete=models.CASCADE,
    )

    def first_answer_choice_label(self):
        return self.question.get_choice_label(self.first_answer_choice)

    first_answer_choice_label.short_description = _("First answer choice")
    first_answer_choice_label.admin_order_field = "first_answer_choice"

    def second_answer_choice_label(self):
        return self.question.get_choice_label(self.second_answer_choice)

    second_answer_choice_label.short_description = _("Second answer choice")
    second_answer_choice_label.admin_order_field = "second_answer_choice"

    def __str__(self):
        return str(
            _("{} for question {}").format(self.id, self.question.title)
        )

    def show_chosen_rationale(self):
        if self.chosen_rationale:
            return self.chosen_rationale.rationale
        else:
            return None

    show_chosen_rationale.short_description = "Display chosen rationale"

    @property
    def correct(self):
        """
        If the second answer is correct in the case where a rationale is
        presented or the first one if not (not implemented).

        Returns
        -------
        bool:
            Answer is correct or not
        """
        if self.question.second_answer_needed:
            if self.second_answer_choice is None:
                return False
            else:
                return self.question.is_correct(self.second_answer_choice)
        else:
            return self.first_correct

    @property
    def first_correct(self):
        """
        If the first answer is correct.

        Returns
        -------
        bool:
            First answer is correct or not
        """
        if self.question.type == "RO":
            return RationaleOnlyQuestion.is_correct(self.first_answer_choice)

        return self.question.is_correct(self.first_answer_choice)

    @property
    def completed(self):
        """
        If the answer corresponds to a completed question.

        Returns
        -------
        bool:
            if the answer corresponds to a completed question.
        """

        if self.question.second_answer_needed:
            return self.second_answer_choice is not None
        else:
            return self.first_answer_choice is not None

    @property
    def grade(self):
        """ Compute grade based on grading scheme of question. """
        if (
            self.question.grading_scheme == GradingScheme.STANDARD
            or isinstance(self.question, RationaleOnlyQuestion)
        ):
            return float(self.correct)
        elif self.question.grading_scheme == GradingScheme.ADVANCED:
            if self.correct and self.first_correct:
                return 1.0
            elif self.correct or self.first_correct:
                return 0.5
            else:
                return 0.0
        else:
            raise NotImplementedError(
                "This grading scheme has not been implemented."
            )

    @property
    def time_first_answer(self):
        """
        Returns the time between the first time the question is shown and the
        first answer.

        Returns
        -------
        timedelta
            Time taken to answer first part
        """
        return self.datetime_first - self.datetime_start

    @property
    def time_second_answer(self):
        """
        Returns the time between the second and first answers.

        Returns
        -------
        timedelta
            Time taken to answer second part
        """
        return self.datetime_second - self.datetime_first


class AnswerVote(models.Model):
    """Vote on a rationale with attached fake attribution."""

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    user_token = models.CharField(max_length=100)
    fake_username = models.CharField(max_length=100)
    fake_country = models.CharField(max_length=100)
    UPVOTE = 0
    DOWNVOTE = 1
    FINAL_CHOICE = 2
    VOTE_TYPE_CHOICES = (
        (UPVOTE, "upvote"),
        (DOWNVOTE, "downvote"),
        (FINAL_CHOICE, "final_choice"),
    )
    vote_type = models.PositiveSmallIntegerField(
        _("Vote type"), choices=VOTE_TYPE_CHOICES
    )


class RationaleOnlyManager(models.Manager):
    def get_by_natural_key(self, title):
        return self.get(title=title)

    def get_queryset(self):
        return (
            super(RationaleOnlyManager, self).get_queryset().filter(type="RO")
        )


class RationaleOnlyQuestion(Question):
    objects = RationaleOnlyManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.question.second_answer_needed = False
        self.question.save()
        super(RationaleOnlyQuestion, self).save(*args, **kwargs)

    def start_form_valid(request, view, form):
        rationale = form.cleaned_data["rationale"]
        datetime_start = form.cleaned_data["datetime_start"]

        # Set first_answer_choice to 0 to indicate null
        answer = Answer(
            question=view.question,
            assignment=view.assignment,
            first_answer_choice=0,
            rationale=rationale,
            user_token=view.user_token,
            datetime_start=datetime_start,
            datetime_first=timezone.now(),
        )
        answer.save()

        view.emit_event(
            "save_problem_success",
            success="correct",
            rationale=rationale,
            grade=answer.grade,
        )
        view.stage_data.clear()

        return

    def get_start_form_class(self):
        from ..forms import RationaleOnlyForm

        return RationaleOnlyForm

    @staticmethod
    def is_correct(*args, **kwargs):
        return True


class ShownRationale(models.Model):
    shown_for_answer = models.ForeignKey(
        Answer, related_name="shown_for_answer", on_delete=models.CASCADE
    )
    shown_answer = models.ForeignKey(
        Answer,
        related_name="shown_answer",
        null=True,
        on_delete=models.CASCADE,
    )


class AnswerAnnotation(models.Model):
    SCORE_CHOICES = (
        (0, _("0-Never Show")),
        (1, _("1-Not Convincing")),
        (2, _("2-Somewhat Convincing")),
        (3, _("3-Very Convincing")),
    )
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    annotator = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    score = models.PositiveIntegerField(
        null=True, default=None, blank=True, choices=SCORE_CHOICES
    )
    note = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return "{}: {} by {}".format(self.answer, self.score, self.annotator)
