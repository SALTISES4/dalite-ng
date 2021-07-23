import base64

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from quality.models import Quality
from reputation.models import Reputation

from .answer import Answer
from .assignment import Assignment
from .group import StudentGroup
from .institution import Institution
from .question import Discipline, Question
from .student import Student, StudentGroupAssignment


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institutions = models.ManyToManyField(Institution, blank=True)
    disciplines = models.ManyToManyField(Discipline, blank=True)
    assignments = models.ManyToManyField(Assignment, blank=True)
    archived_assignments = models.ManyToManyField(
        Assignment, blank=True, related_name="archived_assignments"
    )
    archived_questions = models.ManyToManyField(
        Question, blank=True, related_name="archived_questions"
    )
    deleted_questions = models.ManyToManyField(Question, blank=True)
    favourite_questions = models.ManyToManyField(
        Question, blank=True, related_name="favourite_questions"
    )
    current_groups = models.ManyToManyField(
        StudentGroup, blank=True, related_name="current_groups"
    )
    quality = models.ForeignKey(
        Quality, blank=True, null=True, on_delete=models.SET_NULL
    )
    reputation = models.OneToOneField(
        Reputation, blank=True, null=True, on_delete=models.SET_NULL
    )
    last_dashboard_access = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time the teacher went on their teacher dashboard.",
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

        if last_login is not None:
            activity = (
                Answer.objects.filter(assignment__in=all_assignments)
                .filter(user_token__in=all_current_students)
                .filter(
                    Q(datetime_start__gt=last_login)
                    | Q(datetime_first__gt=last_login)
                    | Q(datetime_second__gt=last_login)
                )
                .count()
            )
        else:
            activity = 0

        return activity

    @staticmethod
    def get(hash_):
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

        return teacher

    @property
    def hash(self):
        return base64.urlsafe_b64encode(
            str(self.user.username).encode()
        ).decode()

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _("teacher")
        verbose_name_plural = _("teachers")


class LastLogout(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_logout = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = ["last_logout"]


class TeacherNotification(models.Model):
    """Generic framework for notifications based on ContentType"""

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    notification_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("notification_type", "object_id")
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "notification_type", "object_id")

    def __str__(self):
        return "{}-{} for {}".format(
            self.notification_type.model, self.object_id, self.teacher
        )


class VerifiedDomain(models.Model):
    domain = models.CharField(
        max_length=100,
        help_text=_(
            "Teacher-only email domain, if available. "
            "Email addresses with these domains will be treated as verified."
        ),
    )
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
