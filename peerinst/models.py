# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import itertools
import smtplib
import string

from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError, models
from django.db.models import Q
from django.template import loader
from django.utils import timezone
from django.utils.encoding import smart_bytes
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from . import rationale_choice
from .students import create_student_token, get_student_username_and_password
from .utils import create_token, verify_token


def no_hyphens(value):
    if "-" in value:
        raise ValidationError(_("Hyphens may not be used in this field."))


class GradingScheme(object):
    STANDARD = 0
    ADVANCED = 1


class Category(models.Model):
    title = models.CharField(
        _("Category Name"),
        unique=True,
        max_length=100,
        help_text=_("Name of a category questions can be sorted into."),
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
        help_text=_("Name of a discipline."),
        validators=[no_hyphens],
    )

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("discipline")
        verbose_name_plural = _("disciplines")


class QuestionManager(models.Manager):
    def get_by_natural_key(self, title):
        return self.get(title=title)


class Question(models.Model):
    objects = QuestionManager()

    id = models.AutoField(
        primary_key=True,
        help_text=_(
            "Use this ID to refer to the question in the LMS. Note: The "
            "question will have to have been saved at least once before an ID "
            "is available."
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
        upload_to="images",
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
            "videos should include transcripts."
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
        blank=True,
        help_text=_(
            "Optional. Select categories for this question.  You can select "
            "multiple categories."
        ),
    )
    discipline = models.ForeignKey(
        Discipline,
        blank=True,
        null=True,
        help_text=_(
            "Optional. Select the discipline to which this question should "
            "be associated."
        ),
    )
    fake_attributions = models.BooleanField(
        _("Add fake attributions"),
        default=False,
        help_text=_(
            "Add random fake attributions consisting of username and country "
            "to rationales. You can configure the lists of fake values and "
            "countries from the start page of the admin interface."
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

    def __unicode__(self):
        if self.discipline:
            return "{} - {}".format(self.discipline, self.title)
        return self.title

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
                "You must provide alternative text for accessibility if providing an image."
            )
            errors.update({"image_alt_text": msg})
        if errors:
            raise exceptions.ValidationError(errors)

    def natural_key(self):
        return (self.title,)

    def get_choice_label_iter(self):
        """Return an iterator over the answer labels with the style determined by answer_style.

        The iterable doesn't stop after the current number of answer choices.
        """
        if self.answer_style == Question.ALPHA:
            return iter(string.ascii_uppercase)
        elif self.answer_style == Question.NUMERIC:
            return itertools.imap(str, itertools.count(1))
        assert False, "The field Question.answer_style has an invalid value."

    def get_choice_label(self, index):
        """Return an answer label for answer index with the style determined by answer_style.

        This method does not check whether index is out of bounds.
        """
        if index is None:
            return None
        elif self.answer_style == Question.ALPHA:
            return string.ascii_uppercase[index - 1]
        elif self.answer_style == Question.NUMERIC:
            return str(index)
        assert False, "The field Question.answer_style has an invalid value."

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

        if self.answerchoice_set.count() > 0:
            student_answers = self.answer_set.filter(expert=False).filter(
                second_answer_choice__gt=0
            )
            N = len(student_answers)
            if N > 0:
                for answer in student_answers:
                    if self.is_correct(answer.first_answer_choice):
                        if self.is_correct(answer.second_answer_choice):
                            matrix[str("easy")] += 1.0 / N
                        else:
                            matrix[str("tricky")] += 1.0 / N
                    else:
                        if self.is_correct(answer.second_answer_choice):
                            matrix[str("peer")] += 1.0 / N
                        else:
                            matrix[str("hard")] += 1.0 / N

        return matrix

    def get_frequency(self):
        choice1 = {}
        choice2 = {}
        frequency = {}
        student_answers = (
            self.answer_set.filter(expert=False)
            .filter(first_answer_choice__gt=0)
            .filter(second_answer_choice__gt=0)
        )
        c = 1
        for answerChoice in self.answerchoice_set.all():
            label = self.get_choice_label(c) + ". " + answerChoice.text
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

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")


class AnswerChoice(models.Model):
    question = models.ForeignKey(Question)
    text = models.CharField(_("Text"), max_length=500)
    correct = models.BooleanField(_("Correct?"))

    def __unicode__(self):
        return self.text

    class Meta:
        ordering = ["id"]
        verbose_name = _("answer choice")
        verbose_name_plural = _("answer choices")


class Assignment(models.Model):
    identifier = models.CharField(
        _("identifier"),
        primary_key=True,
        max_length=100,
        help_text=_(
            "A unique identifier for this assignment used for inclusion in a course."
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
        ### attempt to redirect to assignment-update after assignment-create
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


class Answer(models.Model):
    question = models.ForeignKey(Question)
    assignment = models.ForeignKey(Assignment, blank=True, null=True)
    first_answer_choice = models.PositiveSmallIntegerField(
        _("First answer choice")
    )
    rationale = models.TextField(_("Rationale"))
    second_answer_choice = models.PositiveSmallIntegerField(
        _("Second answer choice"), blank=True, null=True
    )
    chosen_rationale = models.ForeignKey("self", blank=True, null=True)
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
    time = models.DateTimeField(blank=True, null=True)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def first_answer_choice_label(self):
        return self.question.get_choice_label(self.first_answer_choice)

    first_answer_choice_label.short_description = _("First answer choice")
    first_answer_choice_label.admin_order_field = "first_answer_choice"

    def second_answer_choice_label(self):
        return self.question.get_choice_label(self.second_answer_choice)

    second_answer_choice_label.short_description = _("Second answer choice")
    second_answer_choice_label.admin_order_field = "second_answer_choice"

    def __unicode__(self):
        return unicode(
            _("{} for question {}").format(self.id, self.question.title)
        )

    def get_grade(self):
        """ Compute grade based on grading scheme of question. """
        if self.question.grading_scheme == GradingScheme.STANDARD:
            # Standard grading scheme: Full score if second answer is correct
            correct = self.question.is_correct(self.second_answer_choice)
            return float(correct)
        else:
            # Advanced grading scheme: Partial scores for individual answers
            grade = 0.
            if self.question.is_correct(self.first_answer_choice):
                grade += 0.5
            if self.question.is_correct(self.second_answer_choice):
                grade += 0.5
            return grade

    def show_chosen_rationale(self):
        if self.chosen_rationale:
            return self.chosen_rationale.rationale
        else:
            pass

    show_chosen_rationale.short_description = "Display chosen rationale"


class FakeUsername(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = _("fake username")
        verbose_name_plural = _("fake usernames")


class FakeCountry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = _("fake country")
        verbose_name_plural = _("fake countries")


class AnswerVote(models.Model):
    """Vote on a rationale with attached fake attribution."""

    answer = models.ForeignKey(Answer)
    assignment = models.ForeignKey(Assignment)
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


class StudentGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    creation_date = models.DateField(blank=True, null=True, auto_now=True)
    teacher = models.ManyToManyField("Teacher", blank=True)

    def __unicode__(self):
        if not self.title:
            return self.name
        else:
            return self.title

    class Meta:
        ordering = ["-creation_date"]
        verbose_name = _("group")
        verbose_name_plural = _("groups")

    @staticmethod
    def get(hash_):
        assert isinstance(hash_, basestring), "Precondition failed for `hash_`"
        try:
            id_ = int(base64.urlsafe_b64decode(hash_.encode()).decode())
        except UnicodeDecodeError:
            id_ = None
        if id_:
            try:
                group = StudentGroup.objects.get(id=id_)
            except StudentGroup.DoesNotExist:
                group = None
        else:
            group = None

        output = group
        assert output is None or isinstance(
            output, StudentGroup
        ), "Postcondition failed"
        return output

    @property
    def hash(self):
        payload = {"group_name": self.name}
        output = base64.urlsafe_b64encode(str(self.id).encode()).decode()
        assert isinstance(output, basestring), "Postcondition failed"
        return output

    @property
    def students(self):
        return Student.objects.filter(groups=self)

    @property
    def has_emails(self):
        return all(s.student.email for s in self.students)


class Student(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField(StudentGroup, blank=True)

    def __unicode__(self):
        return self.student.username

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")

    @staticmethod
    def get_or_create(email):
        """
        Adds the student by using hashes of the email for the username and
        password.
        """

        assert isinstance(email, basestring), "Precondition failed for `email`"

        student = None

        username, password = get_student_username_and_password(email)

        try:
            student = Student.objects.get(
                student__username=username, student__email=email
            )
        except Student.DoesNotExist:

            try:
                email = email.lower()
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )

                # Set inactive until confirmed by user
                user.is_active = False
                user.save()
                student = Student.objects.create(student=user)
            except IntegrityError:
                student = None

        output = student
        assert output is None or isinstance(
            output, Student
        ), "Postcondition failed"
        return output

    def send_confirmation_email(self, group, host):
        """Sends e-mail with link for confirmation of account."""
        assert isinstance(host, basestring), "Precondition failed for `host`"
        err = None

        if not self.student.email.endswith("localhost"):

            username = self.student.username
            user_email = self.student.email
            token = create_student_token(username, user_email)
            hash_ = group.hash
            link = reverse(
                "confirm-signup-through-link",
                kwargs={"group_hash": hash_, "token": token},
            )

            if host == "localhost" or host == "127.0.0.1":
                protocol = "http"
            else:
                protocol = "https"

            subject = "Confirm myDALITE account"
            message = (
                "Please confirm myDALITE account by going to: " + host + link
            )
            template = "students/email_confirmation.html"
            context = {"link": link, "host": host, "protocol": protocol}

            try:
                send_mail(
                    subject,
                    message,
                    "noreply@myDALITE.org",
                    [user_email],
                    fail_silently=False,
                    html_message=loader.render_to_string(
                        template, context=context
                    ),
                )
            except smtplib.SMTPException:
                err = "There was an error sending the email."

        output = err
        assert err is None or isinstance(
            output, basestring
        ), "Postcondition failed"

    def send_signin_email(self, host):
        assert isinstance(host, basestring), "Precondition failed for `host`"
        err = None

        if not self.student.email.endswith("localhost"):

            username = self.student.username
            user_email = self.student.email
            token = create_student_token(username, user_email)
            groups = self.groups.all()
            assignments = [
                StudentGroupAssignment.objects.filter(group=group)
                for group in groups
            ]
            links = [
                [
                    reverse(
                        "live",
                        kwargs={
                            "assignment_hash": assignment.hash,
                            "token": token,
                        },
                    )
                    for assignment in group
                ]
                for group in assignments
            ]

            if host.startswith("localhost") or host.startswith("127.0.0.1"):
                protocol = "http"
            else:
                protocol = "https"

            subject = "Sign in to your myDALITE account"
            message = (
                "Go to any of your assignments by clicking the links below:\n"
                "\n".join(
                    "\n".join(
                        ["Group: {}".format(group.title)]
                        + [
                            "{}: {}{}{}".format(
                                a.assignment.title, protocol, host, l
                            )
                            for a, l in zip(assignment, link)
                        ]
                    )
                    for group, assignment, link in zip(
                        groups, assignments, links
                    )
                )
            )
            groups = [
                {
                    "title": group.title,
                    "assignments": [
                        {"title": a.assignment.title, "link": l}
                        for a, l in zip(assignment, link)
                    ],
                }
                for group, assignment, link in zip(groups, assignments, links)
            ]
            template = "students/email_signin.html"
            context = {"groups": groups, "host": host, "protocol": protocol}

            try:
                send_mail(
                    subject,
                    message,
                    "noreply@myDALITE.org",
                    [user_email],
                    fail_silently=False,
                    html_message=loader.render_to_string(
                        template, context=context
                    ),
                )
            except smtplib.SMTPException:
                err = "There was an error sending the email."

        output = err
        assert err is None or isinstance(
            output, basestring
        ), "Postcondition failed"

    def send_missing_assignments(self, group, host):
        assert isinstance(
            group, StudentGroup
        ), "Precondition failed for `group`"

        if not self.student.email.endswith("localhost"):

            assignments = StudentGroupAssignment.objects.filter(group=group)

            for assignment in assignments:
                # Create missing instances
                if not StudentAssignment.objects.filter(
                    student=self, group_assignment=assignment
                ).exists():
                    assignment_ = StudentAssignment.objects.create(
                        student=self, group_assignment=assignment
                    )
                    if not assignment.is_expired():
                        # Just send active assignments
                        assignment_.send_email(host, "new_assignment")


class Institution(models.Model):
    name = models.CharField(
        max_length=100, unique=True, help_text=_("Name of school.")
    )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("institution")
        verbose_name_plural = _("institutions")


class VerifiedDomain(models.Model):
    domain = models.CharField(
        max_length=100,
        help_text=_(
            "Teacher-only email domain, if available.  Email addresses with these domains will be treated as verified."
        ),
    )
    institution = models.ForeignKey(Institution)

    def __unicode__(self):
        return self.domain

    class Meta:
        verbose_name = _("verified email domain name")


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institutions = models.ManyToManyField(Institution, blank=True)
    disciplines = models.ManyToManyField(Discipline, blank=True)
    assignments = models.ManyToManyField(Assignment, blank=True)
    deleted_questions = models.ManyToManyField(Question, blank=True)
    favourite_questions = models.ManyToManyField(
        Question, blank=True, related_name="favourite_questions"
    )
    current_groups = models.ManyToManyField(
        StudentGroup, blank=True, related_name="current_groups"
    )

    def get_absolute_url(self):
        return reverse("teacher", kwargs={"pk": self.pk})

    def student_activity(self):
        last_login = self.user.last_login
        current_groups = self.current_groups.all()

        all_current_students = Student.objects.filter(
            groups__in=current_groups
        ).values("student__username")

        all_assignments = StudentGroupAssignment.objects.filter(
            group__in=current_groups
        ).values("assignment")

        activity = (
            Answer.objects.filter(assignment__in=all_assignments)
            .filter(user_token__in=all_current_students)
            .filter(time__gt=last_login)
            .count()
        )

        return activity

    @staticmethod
    def get(hash_):
        assert isinstance(hash_, basestring), "Precondition failed for `hash_`"
        try:
            username = str(base64.urlsafe_b64decode(hash_.encode()).decode())
        except UnicodeDecodeError:
            username = None
        if username:
            try:
                teacher = Teacher.objects.get(user__username=username)
            except Teacher.DoesNotExist:
                teacher = None
        else:
            teacher = None

        output = teacher
        assert output is None or isinstance(
            output, Teacher
        ), "Postcondition failed"
        return output

    @property
    def hash(self):
        output = base64.urlsafe_b64encode(
            str(self.user.username).encode()
        ).decode()
        assert isinstance(output, basestring), "Postcondition failed"
        return output

    def __unicode__(self):
        return self.user.username

    class Meta:
        verbose_name = _("teacher")
        verbose_name_plural = _("teachers")


class BlinkQuestion(models.Model):
    question = models.ForeignKey(Question)
    teacher = models.ForeignKey(Teacher, null=True)
    current = models.BooleanField(default=True)
    active = models.BooleanField(default=False)
    time_limit = models.PositiveSmallIntegerField(_("Time limit"), null=True)
    key = models.CharField(unique=True, max_length=8, primary_key=True)

    def __unicode__(self):
        return self.question.text


class BlinkRound(models.Model):
    question = models.ForeignKey(BlinkQuestion)
    activate_time = models.DateTimeField()
    deactivate_time = models.DateTimeField(null=True)


class BlinkAnswer(models.Model):
    question = models.ForeignKey(BlinkQuestion)
    answer_choice = models.PositiveSmallIntegerField(_("Answer choice"))
    vote_time = models.DateTimeField()
    voting_round = models.ForeignKey(BlinkRound)


class BlinkAssignment(models.Model):
    title = models.CharField(_("Title"), max_length=200)
    teacher = models.ForeignKey(Teacher, null=True)
    blinkquestions = models.ManyToManyField(
        BlinkQuestion, through="BlinkAssignmentQuestion"
    )
    key = models.CharField(unique=True, max_length=8)
    active = models.BooleanField(default=False)

    def __unicode__(self):
        return "{} < {} >".format(
            self.title,
            " ; ".join(
                "rank {} - {}".format(q.rank, q.blinkquestion.question.title)
                for q in self.blinkassignmentquestion_set.all()
            ),
        )

    class Meta:
        verbose_name = _("blink assignment")
        verbose_name_plural = _("blink assignments")


class BlinkAssignmentQuestion(models.Model):
    blinkassignment = models.ForeignKey(
        BlinkAssignment, on_delete=models.CASCADE
    )
    blinkquestion = models.ForeignKey(BlinkQuestion, on_delete=models.CASCADE)
    rank = models.IntegerField()

    ## https://djangosnippets.org/snippets/998/
    def move_down_rank(self):
        try:
            next_q = (
                BlinkAssignmentQuestion.objects.filter(
                    blinkassignment__title=self.blinkassignment.title
                )
                .filter(rank__gt=self.rank)
                .first()
            )

            next_rank = next_q.rank
            next_q.rank = self.rank
            next_q.save()
            self.rank = next_rank
            self.save()

        except IndexError as e:
            pass

        return

    def move_up_rank(self):
        try:
            previous_q = (
                BlinkAssignmentQuestion.objects.filter(
                    blinkassignment__title=self.blinkassignment.title
                )
                .filter(rank__lt=self.rank)
                .last()
            )

            previous_rank = previous_q.rank
            previous_q.rank = self.rank
            previous_q.save()
            self.rank = previous_rank
            self.save()

        except IndexError as e:
            pass

        return

    def renumber(self):
        try:
            all_q = BlinkAssignmentQuestion.objects.filter(
                blinkassignment__title=self.blinkassignment.title
            ).order_by("rank")

            r = 0
            for q in all_q:
                q.rank = r
                q.save()
                r = r + 1

        except IndexError as e:
            pass

        return

    def __unicode__(self):
        return "{} : rank {} - {}-{}".format(
            self.blinkassignment.title,
            self.rank,
            self.blinkquestion.question.id,
            self.blinkquestion.question.title,
        )

    class Meta:
        ordering = ["rank"]

    # Reporting structure
    # Front-end assignment making
    # Sorting by label "easy, tricky, peer, hard"


class LtiEvent(models.Model):
    # question = models.ForeignKey(Question,blank=True,null=True)
    # assignment = models.ForeignKey(Assignment,blank=True,null=True)
    # user = models.ForeignKey(User,blank=True, null=True)
    event_type = models.CharField(max_length=100)
    event_log = JSONField(default={})
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    def __unicode__(self):
        return str(self.timestamp)


class StudentGroupAssignment(models.Model):
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    distribution_date = models.DateTimeField(editable=False, auto_now_add=True)
    due_date = models.DateTimeField(blank=False, default=timezone.now)
    show_correct_answers = models.BooleanField(
        _("Show correct answers"),
        default=True,
        help_text=_(
            "Check if students should be shown correct answer after completing "
            "the question."
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

        for student in Student.objects.filter(groups=self.group):
            assignment, _ = StudentAssignment.objects.get_or_create(
                student=student, group_assignment=self
            )
            assignment.send_email(
                host, mail_type="new_assignment", assignment_hash=self.hash
            )

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = ",".join(
                map(str, range(len(self.assignment.questions.all())))
            )
        super(StudentGroupAssignment, self).save(*args, **kwargs)

    def get_student_progress(self):

        students = self.group.students
        questions = self.questions
        progress = []
        for question in questions:
            progress.append(
                {
                    "question_title": question.title,
                    "n_choices": len(question.get_choices()),
                    "correct": next(
                        i + 1
                        for i, _ in enumerate(question.get_choices())
                        if question.is_correct(i + 1)
                    ),
                    "students": [],
                }
            )
            for student in students:
                answer = Answer.objects.filter(
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
                            == progress[-1]["correct"],
                            "second_correct": None
                            if (answer is None)
                            or (answer.second_answer_choice is None)
                            else answer.second_answer_choice
                            == progress[-1]["correct"],
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


class StudentAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group_assignment = models.ForeignKey(
        StudentGroupAssignment, on_delete=models.CASCADE
    )
    first_access = models.DateTimeField(editable=False, auto_now=True)
    last_access = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        unique_together = ("student", "group_assignment")

    def __unicode__(self):
        return "{} for {}".format(self.group_assignment, self.student)

    def send_email(
        self, host, mail_type="login", link=None, assignment_hash=None
    ):
        assert (
            isinstance(link, basestring) and "{}" in link or link is None
        ), "Precondition failed for `link`"
        assert isinstance(host, basestring), "Precondition failed for `host`"
        assert isinstance(mail_type, basestring) and mail_type in (
            "login",
            "new_assignment",
        ), "Precondition failed for `mail_type`"

        err = None

        if not self.student.student.email.endswith("localhost"):

            username = self.student.student.username
            user_email = self.student.student.email

            if err is None and user_email:
                print(mail_type.upper())

                token = create_student_token(username, user_email)

                if mail_type == "login":

                    subject = "Login to myDALITE"
                    message = "Click link below to login to your account."

                    template = "students/email_login.html"

                elif mail_type == "new_assignment":

                    link = reverse(
                        "live",
                        kwargs={
                            "assignment_hash": self.group_assignment.hash,
                            "token": token,
                        },
                    )

                    subject = (
                        "New assignment in "
                        + self.group_assignment.group.title
                        + " (due "
                        + self.group_assignment.due_date.astimezone(
                            pytz.timezone(settings.DEFAULT_TIMEZONE)
                        ).strftime("%Y-%m-%d %H:%M %Z")
                        + ")"
                    )
                    message = "Click link below to access your assignment."

                    template = "students/email_new_assignment.html"

                else:
                    raise RuntimeError(
                        "This error should not be possible. Check asserts and "
                        "mail types."
                    )

                if host == "localhost" or host == "127.0.0.1":
                    protocol = "http"
                else:
                    protocol = "https"

                context = {"link": link, "host": host, "protocol": protocol}

                try:
                    send_mail(
                        subject,
                        message,
                        "noreply@myDALITE.org",
                        [user_email],
                        fail_silently=False,
                        html_message=loader.render_to_string(
                            template, context=context
                        ),
                    )
                except smtplib.SMTPException:
                    err = "There was an error sending the email."
            else:
                if err is None:
                    err = "There is no email associated with user {}".format(
                        self.student.user.username
                    )

        output = err
        assert err is None or isinstance(
            output, basestring
        ), "Postcondition failed"

    def get_current_question(self):
        questions = self.group_assignment.questions

        # get the answer or None for each question of the assignment
        answers = [
            Answer.objects.filter(
                user_token=self.student.student.username,
                question=question,
                assignment=self.group_assignment.assignment,
            ).first()
            for question in questions
        ]
        has_first_answer = [
            a.first_answer_choice is not None if a else False for a in answers
        ]
        # if a question has at least one missing answer (no first choice or no
        # answer), returns the first question with no answer or no first answer
        # choice
        if not all(has_first_answer):
            output = questions[has_first_answer.index(False)]
        else:
            has_second_answer = [
                a.second_answer_choice is not None for a in answers
            ]
            # if there is a question missing the second answer, returns it or
            # returns None if all questions have been answered twice
            if not all(has_second_answer):
                output = questions[has_second_answer.index(False)]
            else:
                output = None

        assert output is None or isinstance(
            output, Question
        ), "Postcondition failed"
        return output
