import base64
import logging
from datetime import datetime, timedelta

import pytz
from django.contrib.auth.models import User
from django.core import validators
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from quality.models import Quality
from reputation.models import Reputation

from ..tasks import distribute_assignment_to_students_async
from ..util import (
    get_average_time_spent_on_all_question_start,
    student_list_from_student_groups,
)
from ..utils import format_time
from .group import StudentGroup
from .question import Question

logger = logging.getLogger("peerinst-models")


class Assignment(models.Model):
    identifier = models.CharField(
        _("identifier"),
        primary_key=True,
        max_length=100,
        help_text=_(
            "A unique identifier for this assignment used for inclusion in a "
            "course.  Only use letters, numbers and/or the underscore for the "
            "identifier."
        ),
        validators=[validators.validate_slug],
    )
    title = models.CharField(_("Title"), max_length=200)
    questions = models.ManyToManyField(Question, verbose_name=_("Questions"))
    owner = models.ManyToManyField(User, blank=True)
    reputation = models.OneToOneField(
        Reputation, blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.identifier

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
    def editable(self):
        return (
            not self.answer_set.exclude(user_token__exact="").count()
            and not StudentGroupAssignment.objects.filter(
                assignment=self
            ).exists()
        )


class StudentGroupAssignment(models.Model):
    group = models.ForeignKey(
        StudentGroup, on_delete=models.CASCADE, blank=True, null=True
    )
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
        return "{} for {}".format(self.assignment, self.group)

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
                "Student group assignment {}".format(self.pk)
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
                "Student group assignment {}".format(self.pk)
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
            self.group.student_set.count(),
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
            questions = [q.title for q in self.assignment.questions.all()]
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
                map(str, list(range(len(self.assignment.questions.all()))))
            )
        super(StudentGroupAssignment, self).save(*args, **kwargs)

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
    def hash(self):
        return base64.urlsafe_b64encode(str(self.id).encode()).decode()

    @property
    def expired(self):
        return datetime.now(pytz.utc) > self.due_date

    @property
    def questions(self):
        questions_ = self.assignment.questions.all()
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
