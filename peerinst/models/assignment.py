# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
from datetime import datetime
import logging

import pytz
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

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
            "course."
        ),
    )
    title = models.CharField(_("Title"), max_length=200)
    questions = models.ManyToManyField(Question, verbose_name=_("Questions"))
    owner = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
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
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    distribution_date = models.DateTimeField(editable=False, auto_now_add=True)
    due_date = models.DateTimeField(blank=False, default=timezone.now)
    show_correct_answers = models.BooleanField(
        _("Show correct answers"),
        default=True,
        help_text=_(
            "Check if students should be shown correct answer after "
            "completing the question."
        ),
    )
    order = models.TextField(blank=True, editable=False)

    def __unicode__(self):
        return "{} for {}".format(self.assignment, self.group)

    def _verify_order(self, order):
        assert isinstance(order, basestring), "Precondition failed for `order`"

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

        output = err
        assert (output is None) or isinstance(
            output, basestring
        ), "Postcondition failed"
        return output

    def is_expired(self):
        output = datetime.now(pytz.utc) > self.due_date
        assert isinstance(output, bool), "Postcondition failed"
        return output

    def modify_order(self, order):
        err = self._verify_order(order)
        if err is None:
            self.order = order
            self.save()

        output = err
        assert (err is None) or isinstance(
            err, basestring
        ), "Postcondition failed"
        return output

    def get_question(self, idx=None, current_question=None, after=True):
        # Assertions to be revised based on updated template logic
        # assert idx is None or isinstance(
        #     idx, int
        # ), "Precondition failed for `idx`"
        # assert current_question is None or isinstance(
        #     current_question, Question
        # ), "Precondition failed for `current_question`"
        # assert isinstance(after, bool), "Precondition failed for `after`"
        # assert (idx is None) != (
        #     current_question is None
        # ), "Either the `idx` or the `current_question` must be given"

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

        output = question
        assert (output is None) or isinstance(
            output, Question
        ), "Postcondition failed"
        return output

    def send_assignment_emails(self, host):
        assert isinstance(host, basestring), "Precondition failed for `host`"
        logger.debug(
            "Sending assignment emails for student group assignment %d",
            self.pk,
        )

        for student in self.group.student_set.all():
            logger.debug(
                "Sending assignment %d email for student %d",
                self.pk,
                student.pk,
            )
            student.add_assignment(self, host)

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = ",".join(
                map(str, range(len(self.assignment.questions.all())))
            )
        super(StudentGroupAssignment, self).save(*args, **kwargs)

    def get_student_progress(self):
        """
        Returns
        -------
        [
            {
                "question_title": str
                    title of the question,
                "n_choices" : int
                    number of answer choices,
                "correct" : Optional[int]
                    indices of the correct answers (starting at 1),
                "students" : [
                    {
                        "student" :{
                            "username" : str,
                            "email" : str
                        },
                        "answer": {
                            "first" : Optional[int]
                                index of the first answer if answered or None
                                (starting at 1),
                            "second" : Optional[int]
                                index of the second answer if answered or None
                                (starting at 1),
                            "first_correct" : Optional[bool]
                                if not answered, None, else if correct
                            "second_correct" : Optional[bool]
                                if not answered, None, else if correct
                        }

                    }
                ]

            }
        ]
        """

        students = self.group.students
        questions = self.questions
        progress = []
        for question in questions:
            progress.append(
                {
                    "question_title": question.title,
                    "n_choices": len(question.get_choices()),
                    "correct": [
                        i + 1
                        for i, _ in enumerate(question.get_choices())
                        if question.is_correct(i + 1)
                    ],
                    "students": [],
                }
            )
            for student in students:
                answer = self.assignment.answer_set.filter(
                    #  answer = Answer.objects.filter(
                    user_token=student.student.username,
                    question=question,
                    assignment=self.assignment,
                    #  time__gte=self.distribution_date,
                ).first()
                progress[-1]["students"].append(
                    {
                        "student": {
                            "username": student.student.username,
                            "email": student.student.email,
                        },
                        "answer": {
                            "first": answer.first_answer_choice
                            if answer is not None
                            else None,
                            "second": answer.second_answer_choice
                            if (answer is not None)
                            and (answer.second_answer_choice is not None)
                            else None,
                            "first_correct": None
                            if answer is None
                            else answer.first_answer_choice
                            in progress[-1]["correct"],
                            "second_correct": None
                            if (answer is None)
                            or (answer.second_answer_choice is None)
                            else answer.second_answer_choice
                            in progress[-1]["correct"],
                        },
                    }
                )
            progress[-1]["first"] = sum(
                s["answer"]["first"] is not None
                for s in progress[-1]["students"]
            )
            progress[-1]["first_correct"] = sum(
                s["answer"]["first_correct"]
                for s in progress[-1]["students"]
                if s["answer"]["first_correct"] is not None
            )
            progress[-1]["second"] = sum(
                s["answer"]["second"] is not None
                for s in progress[-1]["students"]
            )
            progress[-1]["second_correct"] = sum(
                s["answer"]["second_correct"]
                for s in progress[-1]["students"]
                if s["answer"]["second_correct"] is not None
            )

        output = progress
        return output

    @staticmethod
    def get(hash_):
        assert isinstance(hash_, basestring), "Precondition failed for `hash_`"
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

        output = assignment
        assert output is None or isinstance(
            output, StudentGroupAssignment
        ), "Postcondition failed"
        return output

    @property
    def hash(self):
        output = base64.urlsafe_b64encode(str(self.id).encode()).decode()
        assert isinstance(output, basestring), "Postcondition failed"
        return output

    @property
    def questions(self):
        questions_ = self.assignment.questions.all()
        questions = [questions_[i] for i in map(int, self.order.split(","))]
        return questions
