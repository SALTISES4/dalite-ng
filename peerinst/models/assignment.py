import base64
import logging
from datetime import datetime, timedelta

import bleach
import pytz
from django.contrib.auth.models import User
from django.core import validators
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from peerinst.tasks import distribute_assignment_to_students_async
from peerinst.templatetags.bleach_html import ALLOWED_TAGS
from peerinst.util import (
    get_average_time_spent_on_all_question_start,
    student_list_from_student_groups,
)
from peerinst.utils import format_time
from quality.models import Quality
from reputation.models import Reputation

from .group import StudentGroup
from .question import Question

logger = logging.getLogger("peerinst-models")


class Assignment(models.Model):
    identifier = models.CharField(
        _("identifier"),
        primary_key=True,
        max_length=100,
        help_text=_(
            "The assignment identifier is used to access the assignment "
            "through an LMS (e.g. Moodle).  Only use letters, numbers and the "
            "underscore for the identifier.  Max length is 100 characters."
        ),
        validators=[
            validators.validate_slug,
            validators.MinLengthValidator(2),
        ],
    )
    title = models.CharField(
        _("Title"),
        max_length=200,
        help_text=_(
            "The assignment title can be anything you'd like, but it is "
            "helpful for indexing if it is a descriptive phrase, e.g. "
            "'Mechanics - Energy Diagrams 1'.  Max length is 200 characters."
        ),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_(
            "Notes you would like keep for yourself (or other teachers) "
            "regarding this assignment."
        ),
    )
    intro_page = models.TextField(
        _("Assignment Cover Page"),
        blank=True,
        null=True,
        help_text=_(
            "Any special instructions you would like students to read before "
            "they start the assignment."
        ),
    )
    conclusion_page = models.TextField(
        _("Post Assignment Notes"),
        blank=True,
        null=True,
        help_text=_(
            "Any notes you would like to leave for students to read that will "
            "be shown after the last question of the assignment."
        ),
    )
    questions = models.ManyToManyField(
        Question, verbose_name=_("Questions"), through="AssignmentQuestions"
    )
    owner = models.ManyToManyField(User, blank=True)
    parent = models.ForeignKey(
        "Assignment", blank=True, null=True, on_delete=models.SET_NULL
    )
    reputation = models.OneToOneField(
        Reputation, blank=True, null=True, on_delete=models.SET_NULL
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.identifier

    def save(self, *args, **kwargs):
        html_fields = ["conclusion_page", "description", "intro_page"]
        text_fields = ["title"]

        for field in html_fields:
            if getattr(self, field):
                """Bleach"""
                setattr(
                    self,
                    field,
                    bleach.clean(
                        getattr(self, field),
                        tags=ALLOWED_TAGS,
                        strip=True,
                    ).strip(),
                )
        for field in text_fields:
            if getattr(self, field):
                """Bleach"""
                setattr(
                    self,
                    field,
                    bleach.clean(
                        getattr(self, field),
                        tags=[],
                        strip=True,
                    ).strip(),
                )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "question-list", kwargs={"assignment_id": self.identifier}
        )
        # attempt to redirect to assignment-update after assignment-create
        # return reverse('assignment-update',kwargs={'assignment_id': self.pk})

    class Meta:
        verbose_name = _("assignment")
        verbose_name_plural = _("assignments")

    @property
    def answer_count(self):
        return sum(q.answer_count for q in self.questions.all())

    @property
    def editable(self):
        return (
            not self.answer_set.filter(expert=False)
            .exclude(user_token__exact="")
            .count()
            and not StudentGroupAssignment.objects.filter(
                assignment=self
            ).exists()
        )

    @property
    def is_valid(self):
        return not any(
            [
                Question.is_missing_answer_choices(self.questions.all()),
                Question.is_missing_sample_answers(self.questions.all()),
                Question.is_flagged(self.questions.all()),
            ]
        )


class AssignmentQuestions(models.Model):
    assignment = models.ForeignKey(Assignment, models.DO_NOTHING)
    question = models.ForeignKey(Question, models.DO_NOTHING)
    rank = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.assignment.pk}-{self.question.pk}-{self.rank}"

    class Meta:
        db_table = "peerinst_assignment_questions"
        ordering = ("rank",)
        unique_together = (("assignment", "question"),)


class StudentGroupAssignment(models.Model):
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    distribution_date = models.DateTimeField(
        editable=False, null=True, blank=True
    )
    due_date = models.DateTimeField(blank=False, default=timezone.now)
    show_correct_answers = models.BooleanField(
        _("Show correct answers"),
        default=True,
        help_text=_(
            "Check if students should be shown correct answer after "
            "completing the question."
        ),
    )
    order = models.TextField(blank=True, editable=True)
    reminder_days = models.PositiveIntegerField(default=3)
    quality = models.ForeignKey(
        Quality, blank=True, null=True, on_delete=models.SET_NULL
    )

    def get_absolute_url(self):
        return reverse("group-assignment", args=(self.hash,))

    @staticmethod
    def get(hash_):
        try:
            id_ = int(base64.urlsafe_b64decode(hash_.encode()).decode())
        except UnicodeDecodeError:
            id_ = None
        if id_:
            try:
                assignment = StudentGroupAssignment.objects.get(id=id_)
            except StudentGroupAssignment.DoesNotExist:
                assignment = None
        else:
            assignment = None

        return assignment

    def __str__(self):
        return f"{self.assignment} for {self.group}"

    def _verify_order(self, order):
        n = len(self.assignment.questions.all())

        err = None

        try:
            order_ = list(map(int, order.split(",")))
        except ValueError:
            err = "Given `order` isn't a comma separated list of integers."

        if err is None and any(x < 0 for x in order_):
            err = "Given `order` has negative values."

        if err is None and any(x >= n for x in order_):
            err = (
                "Given `order` has at least one value bigger than "
                "the number of questions."
            )

        if err is None and len(set(order_)) != len(order_):
            err = "There are duplicate values in `order`."

        return err

    def _modify_due_date(self, due_date):
        """
        Modifies the due date.

        Parameters
        ----------
        due_date : str
            String in the format "%Y-%m-%dT%H:%M:%S(.%f)?"

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        err = None
        prev_due_date = self.due_date
        try:
            self.due_date = datetime.strptime(
                due_date[:19], "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=pytz.utc)
        except ValueError:
            err = (
                "The given due date wasn't in the format "
                '"%Y-%m-%dT%H:%M:%S(.%f)?"'
            )
            logger.error(err)
        else:
            self.save()
            logger.info(
                f"Student group assignment {self.pk}"
                + " due date updated to {} from {}.".format(
                    self.due_date, prev_due_date
                )
            )
        return err

    def _modify_order(self, order):
        """
        Modifies the question order.

        Parameters
        ----------
        order : str
            New order as a string of indices separated by commas

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        err = self._verify_order(order)
        if err is None:
            prev_order = self.order
            self.order = order
            self.save()
            logger.info(
                f"Student group assignment {self.pk}"
                + " order updated to {} from {}.".format(
                    self.order, prev_order
                )
            )
        else:
            logger.error(err)

        return err

    def get_question(self, idx=None, current_question=None, after=True):
        question = None

        if idx is None:
            questions = self.questions
            try:
                idx = questions.index(current_question)

                try:
                    if after:
                        if idx < len(questions) - 1:
                            question = questions[idx + 1]
                        else:
                            question = None
                    else:
                        if idx > 0:
                            question = questions[idx - 1]
                        else:
                            question = None
                except IndexError:
                    question = None

            except ValueError:
                question = None

        else:
            questions = self.questions
            if 0 <= idx < len(questions):
                question = questions[idx]
            else:
                question = None

        return question

    def distribute(self):
        self.distribution_date = datetime.now(pytz.utc)
        self.save()
        logger.info("Student group assignment %d distributed", self.pk)
        self.update_students()

    def update_students(self):
        logger.info(
            "Updating %d students for student group assignment %d",
            self.group.students.all().count(),
            self.pk,
        )
        distribute_assignment_to_students_async(self.pk)

    def update(self, name, value):
        """
        Updates the assignment using the given `name` to assign the new
        `value`.

        Parameters
        ----------
        name : str
            Name indicating what to change. One of:
                "due_date"
                "question_list"

        value : Any
            New value of the field
        host : Optional[str] (default : None)
            Hostname of the server to be able to send emails (emails aren't
            sent if None)

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        name = str(name)
        err = None
        if name == "due_date":
            self._modify_due_date(value)

        elif name == "question_list":
            questions = [
                q.title
                for q in self.assignment.questions.order_by(
                    "assignmentquestions__rank"
                )
            ]
            order = ",".join(str(questions.index(v)) for v in value)
            err = self._modify_order(order)
            if err is not None:
                err = (
                    "There was an error changing the question order. "
                    "The problem will soon be resolved."
                )
        else:
            err = "An invalid name was sent."

        if err is None:
            for assignment in self.studentassignment_set.all():
                assignment.send_email("assignment_updated")

        return err

    def check_reminder_status(self):
        """
        Verifies the assignment due date and if the assignment is not finished
        and the due date is sooner or equal to the number reminder days,
        the student notification is updated and an email if possibly sent.

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        err = None
        time_until_expiry = self.due_date - datetime.now(pytz.utc)
        if (
            timedelta()
            < time_until_expiry
            <= timedelta(days=self.reminder_days)
        ):
            errs = []
            for assignment in self.studentassignment_set.all():
                errs.append(
                    assignment.send_reminder(
                        last_day=time_until_expiry <= timedelta(days=1)
                    )
                    or ""
                )
            err = "\n".join(errs) if any(errs) else None
        return err

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = ",".join(
                map(
                    str,
                    list(
                        range(
                            len(
                                self.assignment.questions.order_by(
                                    "assignmentquestions__rank"
                                )
                            )
                        )
                    ),
                )
            )
        super().save(*args, **kwargs)

    @property
    def student_progress(self):
        """
        Returns
        -------
        [
            {
                "question_title": str
                    title of the question,
                "n_students": int
                    number of students
                "n_completed": int
                    number of completed questions
                "n_first_correct": Optional[int]
                    number of correct first answers
                "n_correct": int
                    number of correct answers

            }
        ]
        """
        results = [
            student_assignment.detailed_results
            for student_assignment in self.studentassignment_set.all()
        ]

        return [
            {
                "question_id": question.id,
                "question_title": question.title,
                "n_students": len(results),
                "n_completed": sum(
                    result[i]["completed"] for result in results
                ),
                "n_first_correct": sum(
                    result[i]["first_correct"] for result in results
                ),
                "n_correct": sum(result[i]["correct"] for result in results),
                "time_spent": format_time(
                    get_average_time_spent_on_all_question_start(
                        student_list=student_list_from_student_groups(
                            group_list=[self.group.pk]
                        ),
                        question_id=question.pk,
                    )
                ),
            }
            for i, question in enumerate(self.questions)
        ]

    @property
    def percent_completion(self):
        from peerinst.models import Answer

        # Return value between 0 and 1
        return (
            Answer.objects.filter(assignment=self.assignment)
            .filter(
                user_token__in=self.group.students.values_list(
                    "student__username", flat=True
                )
            )
            .count()
            / (self.studentassignment_set.count() or 1)
            / (len(self.questions) or 1)
        )

    @property
    def hash(self):
        return base64.urlsafe_b64encode(str(self.id).encode()).decode()

    @property
    def expired(self):
        return datetime.now(pytz.utc) > self.due_date

    @property
    def questions(self):
        questions_ = self.assignment.questions.order_by(
            "assignmentquestions__rank"
        )
        if not self.order:
            self.order = ",".join(map(str, list(range(len(questions_)))))
            self.save()
        if questions_:
            questions_ = [
                questions_[i] for i in map(int, self.order.split(","))
            ]
        return questions_

    @property
    def days_to_expiry(self):
        return max(self.due_date - datetime.now(pytz.utc), timedelta()).days

    @property
    def is_distributed(self):
        if self.distribution_date:
            return self.distribution_date < datetime.now(pytz.utc)
        return False

    @property
    def link(self):
        return reverse(
            "group-assignment", kwargs={"assignment_hash": self.hash}
        )

    @property
    def last_modified(self):
        questions = self.questions
        students = [
            assignment.student.student.username
            for assignment in self.studentassignment_set.iterator()
        ]
        return max(
            answer.datetime_second
            if answer.datetime_second
            else answer.datetime_first
            if answer.datetime_first
            else answer.datetime_start
            for question in questions
            for answer in question.answer_set.filter(
                user_token__in=students
            ).exclude(datetime_start__isnull=True)
        )
