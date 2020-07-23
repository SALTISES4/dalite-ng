import logging
from datetime import datetime
from operator import itemgetter

import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import IntegrityError, models
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from reputation.models import Reputation

from ..students import create_student_token, get_student_username_and_password
from ..tasks import send_mail_async
from .answer import Answer, ShownRationale
from .assignment import StudentGroupAssignment
from .group import StudentGroup

logger = logging.getLogger("peerinst-models")


class Student(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField(StudentGroup, blank=True)
    student_groups = models.ManyToManyField(
        StudentGroup,
        blank=True,
        through="StudentGroupMembership",
        related_name="groups_new",
    )
    send_reminder_email_every_day = models.BooleanField(default=False)
    send_reminder_email_day_before = models.BooleanField(default=True)
    reputation = models.OneToOneField(
        Reputation, blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.student.email

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")

    @staticmethod
    def get_or_create(email):
        """
        Gets the student with the given `email`, creating them if need be.

        Parameters
        ----------
        email : str
            Student email

        Returns
        -------
        student : Optional[Student]
            Student instance if no error getting or creating them
        created : bool
            If the student was created or not
        """
        student = None

        email = email.lower()

        username, password = get_student_username_and_password(email)

        try:
            student = Student.objects.get(
                student__username=username, student__email=email
            )
            created = False
        except Student.DoesNotExist:

            try:
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )

                # Set inactive until confirmed by user
                user.is_active = False
                user.save()
                student = Student.objects.create(student=user)
                created = True
            except IntegrityError:
                student = None
                created = False
                logger.error(
                    "There was an error creating student with "
                    "email {}.".format(email)
                )

        return student, created

    def send_email(self, mail_type, group=None, request=None):
        """
        Sends an email to announce a new assignment or an assignment update.

        Parameters
        ----------
        mail_type : str
            Type of mail to send. One of:
                "signin"
                "confirmation"
                "new_group"

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        if group is None and "group" in mail_type:
            msg = "A group is needed for the `mail_type` {}.".format(mail_type)
            logger.error(msg)
            raise ValueError(msg)

        err = None

        if not self.student.email.endswith("localhost"):

            username = self.student.username
            user_email = self.student.email

            if not user_email:
                err = "There is no email associated with user {}.".format(
                    self.student.username
                )
                logger.error(err)

            else:

                host = settings.ALLOWED_HOSTS[0]

                if host == "localhost" or host == "127.0.0.1":
                    protocol = "http"
                    host = "{}:{}".format(host, settings.DEV_PORT)
                else:
                    protocol = "https"

                token = create_student_token(username, user_email)

                signin_link = "{}://{}{}?token={}".format(
                    protocol, host, reverse("student-page"), token
                )

                group = group.title if group is not None else None

                if mail_type == "signin":
                    subject = "Sign in to your myDALITE account"
                    message = (
                        "Sign in to your myDALITE accout by going to "
                        "the link below:\n" + signin_link
                    )
                    template = "peerinst/student/emails/signin.html"
                elif mail_type == "confirmation":
                    subject = "Confirm your myDALITE account"
                    message = (
                        "Please confirm your myDALITE account by going to "
                        "the link below:\n " + signin_link
                    )
                    template = "peerinst/student/emails/confirmation.html"
                elif mail_type == "new_group":
                    subject = (
                        "You've successfully been registered to group " + group
                    )
                    message = (
                        "Sign in to your myDALITE accout by going to "
                        "the link below:\n" + signin_link
                    )
                    template = "peerinst/student/emails/new_group.html"
                else:
                    err = "The `mail_type` wasn't in the allowed types."
                    logger.error(err)

                context = {"signin_link": signin_link, "group": group}

                if err is None:
                    send_mail_async(
                        subject,
                        message,
                        "noreply@myDALITE.org",
                        [user_email],
                        fail_silently=False,
                        html_message=loader.render_to_string(
                            template, context=context
                        ),
                    )

        return err

    def join_group(self, group, mail_type=None):
        """
        Join the given group, adding missing assignments and sending an email.

        Parameters
        ----------
        group : StudentGroup
            Group to join
        mail_type : Optional[str] (default : None)
            Type of mail to send if present. One of:
                "confirmation"
                "new_group"
        """
        try:
            membership = StudentGroupMembership.objects.get(
                student=self, group=group
            )
            membership.current_member = True
            membership.save()
            logger.info(
                "Student %d added back to group %d.", self.pk, group.pk
            )
        except StudentGroupMembership.DoesNotExist:
            StudentGroupMembership.objects.create(
                student=self, group=group, current_member=True
            )
            logger.info(
                "Student %d added to group %d for the first time.",
                self.pk,
                group.pk,
            )

        for assignment in StudentGroupAssignment.objects.filter(
            group=group, distribution_date__isnull=False
        ):
            self.add_assignment(assignment, send_email=False)

        if mail_type is not None:
            self.send_email(mail_type, group=group)

        # TODO to remove eventually when groups are fully integrated in
        # group membership
        self.groups.add(group)

    def leave_group(self, group):
        try:
            membership = StudentGroupMembership.objects.get(
                student=self, group=group
            )
            membership.current_member = False
            membership.save()
        except StudentGroupMembership.DoesNotExist:
            logger.warning(
                "Student {} left group {} of which he wasn't a member.".format(
                    self.pk, group.pk
                )
            )

    def add_assignment(self, group_assignment, send_email=True):
        """
        Adds the `group_assignment` for the student by creating a
        StudentAssignment instance and sending an email informing them of it.

        Parameters
        ----------
        group_assignment : StudentGroupAssignment
            Assignment to add
        send_email : bool (default : True)
            If a new assignment email should be sent

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        assignment, created = StudentAssignment.objects.get_or_create(
            student=self, group_assignment=group_assignment
        )
        if created:
            logger.info(
                "Assignment %d created for student %d.", assignment.pk, self.pk
            )
        else:
            logger.info(
                "Assignment %d retrieved for student %d.",
                assignment.pk,
                self.pk,
            )

        StudentNotification.create(
            type_="new_assignment",
            student=self,
            assignment=assignment,
            expiration=group_assignment.due_date,
        )

        if send_email:
            err = assignment.send_email(mail_type="new_assignment")
        else:
            err = None

        return err

    def evaluate_reputation(self, criterion=None):
        """
        Calculates the reputation for the student on all criteria or on a
        specific criterion, creating the Reputation for them if it doesn't
        already exist.

        Parameters
        ----------
        criterion : Optional[str] (default : none)
            Criterion on which to evaluate

        Returns
        -------
        float
            Evaluated reputation

        Raises
        ------
        ValueError
            If the given criterion isn't part of the list for this reputation
            type
        """
        if self.reputation is None:
            self.reputation = Reputation.create("student")
            self.save()
        return self.reputation.evaluate(criterion)[0]

    @property
    def current_groups(self):
        # TODO add lti_student groups
        return [
            g.group
            for g in StudentGroupMembership.objects.filter(
                student=self, current_member=True
            )
        ]

    @property
    def old_groups(self):
        # TODO add lti_student groups
        return [
            g.group
            for g in StudentGroupMembership.objects.filter(
                student=self, current_member=False
            )
        ]

    @property
    def notifications(self):
        return self.studentnotification_set.order_by("-created_on").all()

    @property
    def answers(self):
        return Answer.objects.filter(user_token=self.student.username)

    @property
    def answers_chosen_by_others(self):
        return Answer.objects.filter(
            chosen_rationale_id__in=self.answers.values_list("pk", flat=True)
        )

    @property
    def answers_shown_to_others(self):
        return ShownRationale.objects.filter(shown_answer__in=self.answers)

    @property
    def answers_also_chosen_by_others(self):
        chosen_by_student = self.answers.exclude(
            chosen_rationale_id__isnull=True
        ).values_list("chosen_rationale_id", flat=True)

        return (
            Answer.objects.exclude(chosen_rationale_id__isnull=True)
            .exclude(pk__in=self.answers)
            .filter(chosen_rationale_id__in=chosen_by_student)
        )

    @property
    def convincing_rationale_reputation(self):
        if self.reputation is None:
            self.reputation = Reputation.create("student")
            self.save()

        return self.reputation.evaluate("convincing_rationales")[0]


class StudentGroupMembership(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    current_member = models.BooleanField(default=True)
    send_emails = models.BooleanField(default=True)
    student_school_id = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "group")


class StudentAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group_assignment = models.ForeignKey(
        StudentGroupAssignment, on_delete=models.CASCADE
    )
    first_access = models.DateTimeField(editable=False, auto_now=True)
    last_access = models.DateTimeField(editable=False, auto_now=True)
    reminder_sent = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ("student", "group_assignment")

    def __str__(self):
        return "{} for {}".format(self.group_assignment, self.student)

    def send_email(self, mail_type):
        """
        Sends an email to announce a new assignment or an assignment update.

        Parameters
        ----------
        mail_type : str
            Type of mail to send. One of:
                "new_assignment"
                "assignment_updated"
                "assignment_about_to_expire"

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        err = None

        if not self.student.student.email.endswith("localhost"):

            username = self.student.student.username
            user_email = self.student.student.email
            group_membership = StudentGroupMembership.objects.get(
                student=self.student, group=self.group_assignment.group
            )

            if not user_email:
                err = "There is no email associated with user {}.".format(
                    self.student.student.username
                )
                logger.error(err)
            elif (
                group_membership.send_emails
                and group_membership.current_member
            ):

                host = settings.ALLOWED_HOSTS[0]

                if host == "localhost" or host == "127.0.0.1":
                    protocol = "http"
                    host = "{}:{}".format(host, settings.DEV_PORT)
                else:
                    protocol = "https"

                token = create_student_token(username, user_email)

                signin_link = "{}://{}{}?token={}".format(
                    protocol, host, reverse("student-page"), token
                )
                assignment_link = "{}://{}{}".format(
                    protocol,
                    host,
                    reverse(
                        "live",
                        kwargs={
                            "assignment_hash": self.group_assignment.hash,
                            "token": token,
                        },
                    ),
                )

                days_to_expiry = self.group_assignment.days_to_expiry

                if mail_type == "new_assignment":
                    subject = "New assignment for group {}".format(
                        self.group_assignment.group.title
                    )
                    message = (
                        "Use one of the links below to access your "
                        "assignment or go to your student page."
                        "\nGo to assignment: "
                        + assignment_link
                        + "\nGo to student page: "
                        + signin_link
                    )
                    template = "peerinst/student/emails/new_assignment.html"

                elif mail_type == "assignment_updated":
                    subject = "Assignment {} for group {} updated".format(
                        self.group_assignment.assignment.title,
                        self.group_assignment.group.title,
                    )
                    message = (
                        "Use one of the links below to access your "
                        "assignment or go to your student page."
                        "\nGo to assignment: "
                        + assignment_link
                        + "\nGo to student page: "
                        + signin_link
                    )
                    template = (
                        "peerinst/student/emails/assignment_updated.html"
                    )

                elif mail_type == "assignment_about_to_expire":
                    if days_to_expiry:
                        subject = "Assignment {} for ".format(
                            self.group_assignment.assignment.title
                        ) + "group {} expires in {} days".format(
                            self.group_assignment.group.title, days_to_expiry
                        )
                    else:
                        subject = "Assignment {} for ".format(
                            self.group_assignment.assignment.title
                        ) + "group {} expires today".format(
                            self.group_assignment.group.title
                        )
                    message = (
                        "Use one of the links below to access your "
                        "assignment or go to your student page."
                        "\nGo to assignment: "
                        + assignment_link
                        + "\nGo to student page: "
                        + signin_link
                    )
                    template = (
                        "peerinst/student/emails/"
                        "assignment_about_to_expire.html"
                    )

                else:
                    err = "The `mail_type` wasn't in the allowed types."
                    logger.error(err)

                context = {
                    "group": self.group_assignment.group.title,
                    "assignment": self.group_assignment.assignment.title,
                    "assignment_link": assignment_link,
                    "signin_link": signin_link,
                    "days_to_expiry": days_to_expiry,
                }

                if err is None:
                    send_mail_async(
                        subject,
                        message,
                        "noreply@myDALITE.org",
                        [user_email],
                        fail_silently=False,
                        html_message=loader.render_to_string(
                            template, context=context
                        ),
                    )
                    logger.info(
                        "Email of type %s sent for student assignment %d",
                        mail_type,
                        self.pk,
                    )

        return err

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

        return output

    def send_reminder(self, last_day):
        """
        Sends a reminder that the assignment is almost due as a reset of the
        student notification and possibly an email.

        Parameters
        ----------
        last_day : bool
            If there is only one day before the assignment is due

        Returns
        -------
        err : Optional[str]
            Error message if there is any
        """
        err = None
        if not self.completed:
            if not StudentNotification.objects.filter(
                student=self.student,
                notification__type="assignment_about_to_expire",
            ).exists():
                StudentNotification.create(
                    type_="assignment_about_to_expire",
                    student=self.student,
                    assignment=self,
                    expiration=self.group_assignment.due_date,
                )

            if StudentGroupMembership.objects.get(
                student=self.student, group=self.group_assignment.group
            ).send_emails:
                if (
                    not self.reminder_sent
                    or self.student.send_reminder_email_every_day
                    or (
                        last_day
                        and self.student.send_reminder_email_day_before
                    )
                ):
                    err = self.send_email("assignment_about_to_expire")
                    if err is None:
                        self.reminder_sent = True
                        self.save()
        return err

    @property
    def completed(self):
        """
        Returns
        -------
        bool
            If the assignment was completed
        """
        if self.first_access.year > 2020 and self.first_access.month > 6:
            return not any(
                not Answer.objects.filter(
                    student_group_assignment=self,
                    assignment=self.group_assignment.assignment,
                    user_token=self.student.student.username,
                    question=question,
                ).exists()
                or not Answer.objects.filter(
                    student_group_assignment=self,
                    assignment=self.group_assignment.assignment,
                    user_token=self.student.student.username,
                    question=question,
                )
                .last()
                .completed
                for question in self.group_assignment.questions
            )
        else:
            return not any(
                not Answer.objects.filter(
                    assignment=self.group_assignment.assignment,
                    user_token=self.student.student.username,
                    question=question,
                ).exists()
                or not Answer.objects.filter(
                    assignment=self.group_assignment.assignment,
                    user_token=self.student.student.username,
                    question=question,
                )
                .last()
                .completed
                for question in self.group_assignment.questions
            )

    @property
    def detailed_results(self):
        """
        Returns the student's results for each question.

        Returns
        -------
        Dict[str, Any]:
            [
                {
                    "completed" : bool
                        if completed
                    "first_correct" : Optional[bool]
                        if first answer correct (or None if not applicable)
                    "correct" : bool
                        if answer correct
                }
            ]
        """
        if self.first_access.year > 2020 and self.first_access.month > 6:
            answers = [
                (
                    Answer.objects.filter(
                        student_group_assignment=self,
                        assignment=self.group_assignment.assignment,
                        user_token=self.student.student.username,
                        question=question,
                    )
                    or [None]
                )[0]
                for question in self.group_assignment.questions
            ]
        else:
            answers = [
                (
                    Answer.objects.filter(
                        assignment=self.group_assignment.assignment,
                        user_token=self.student.student.username,
                        question=question,
                    )
                    or [None]
                )[0]
                for question in self.group_assignment.questions
            ]

        return [
            {
                "completed": answer is not None and answer.completed,
                "first_correct": answer is not None and answer.first_correct,
                "correct": answer is not None and answer.correct,
                "grade": 0 if answer is None else answer.grade,
            }
            for answer in answers
        ]

    @property
    def results(self):
        """
        Returns the student's results aggregated on all questions.

        Returns
        -------
        Dict[str, Any]:
            {
                "n" : int
                    number of questions
                "n_completed" : int
                    number of questions completed
                "n_first_correct" : Optional[int]
                    number of correct first answers (or None if not applicable)
                "n_correct" : int
                    number of correct answers
            }
        """
        results = self.detailed_results
        return {
            "n": len(results),
            "n_completed": sum(map(itemgetter("completed"), results)),
            "n_first_correct": sum(map(itemgetter("first_correct"), results)),
            "n_correct": sum(map(itemgetter("correct"), results)),
            "grade": sum(map(itemgetter("grade"), results)),
        }

    @property
    def grade(self):
        return sum(map(itemgetter("grade"), self.detailed_results))


class StudentNotificationType(models.Model):
    type = models.CharField(max_length=32, unique=True)
    icon = models.TextField()

    def __str__(self):
        return self.type


class StudentNotification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    notification = models.ForeignKey(
        StudentNotificationType, on_delete=models.CASCADE
    )
    created_on = models.DateTimeField(auto_now=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    text = models.TextField()
    expiration = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{} for {}".format(self.notification, self.student)

    @staticmethod
    def create(type_, student, assignment=None, expiration=None):
        """
        Creates a new notification of the given `type_` for the `student`.

        Parameters
        ----------
        type_ : str
            Type of notification. Must be equal to the field `type` for one of
            the StudentNotificationType
        student : Student
            Student for whom the notification is created
        assignment : Optional[StudentAssignment] (default : None)
            Assignment corresponding to the notification if needed
        expiration : Optional[datetime.datetime] (default : None)
            Expiration time

        Raises
        ------
        ValueError
            If the assignment is needed by the current `type_` and isn't given
        NotImplementedError
            If the branch for the given `type_` isn't implemented
        """
        try:
            notification = StudentNotificationType.objects.get(type=type_)
        except StudentNotificationType.DoesNotExist:
            logger.error(
                "A notification wasn't created for "
                + "student {} ".format(student.pk)
                + "because {} wasn't a valid notification type.".format(type_)
            )

        else:

            if assignment is None and "assignment" in type_:
                msg = "An assignment is needed for type {}.".format(type_)
                logger.error(msg)
                raise ValueError(msg)

            if assignment is not None:
                link = reverse(
                    "live",
                    kwargs={
                        "assignment_hash": assignment.group_assignment.hash,
                        "token": create_student_token(
                            student.student.username, student.student.email
                        ),
                    },
                )
            else:
                link = ""

            if type_ == "new_assignment":
                text = "A new assignment {} was added for group {}.".format(
                    assignment.group_assignment.assignment.title,
                    assignment.group_assignment.group.title,
                )

            elif type_ == "assignment_due_date_changed":
                text = (
                    "The due date for assignment {} ".format(
                        assignment.group_assignment.assignment.title
                    )
                    + "in group {} was ".format(
                        assignment.group_assignment.group.title
                    )
                    + "changed to {}.".format(
                        assignment.group_assignment.due_date.strftime(
                            "%Y-%m-%d %H:%M"
                        )
                    )
                )

            elif type_ == "assignment_about_to_expire":
                text = "The assignment {} in group {} expires on {}.".format(
                    assignment.group_assignment.assignment.title,
                    assignment.group_assignment.group.title,
                    assignment.group_assignment.due_date.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                )

            else:
                msg = (
                    "There's a missing branch for notification "
                    "type {}.".format(type_)
                )
                logger.error(msg)
                raise NotImplementedError(msg)

            if not StudentNotification.objects.filter(
                student=student,
                notification=notification,
                link=link,
                text=text,
            ).exists():
                StudentNotification.objects.create(
                    student=student,
                    notification=notification,
                    link=link,
                    text=text,
                    expiration=expiration,
                )
            logger.info(
                "Notification of type {} was created for student {}.".format(
                    type_, student.pk
                )
            )

    @staticmethod
    def clean(student=None):
        """
        Removes the expired notifications for the given student or all
        students.

        Parameters
        ----------
        student : Optional[Student] (default : None)
            Student for whom to remove the notifications
        """
        if student is None:
            StudentNotification.objects.filter(
                expiration__isnull=False
            ).filter(expiration__lt=datetime.now(pytz.utc)).delete()

        else:
            StudentNotification.objects.filter(
                student=student, expiration__isnull=False
            ).filter(expiration__lt=datetime.now(pytz.utc)).delete()
