import logging
from urllib.parse import urlparse

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.db.models import Q
from lti_provider.auth import LTIBackend
from pylti.common import LTIException

from .models import Institution, InstitutionalLMS, StudentGroup, Teacher
from .models.group import current_semester, current_year

logger = logging.getLogger(__name__)

username_field = get_user_model().USERNAME_FIELD


class LTIBackendStudentsOnly(LTIBackend):
    def find_user(self, request, lti):
        # Search for users but exclude staff, superuser, and teacher accounts
        # as well as standalone student accounts

        # find the user via lms identifier first
        kwargs = {username_field: lti.user_identifier(request)}
        user_model = get_user_model()
        user = (
            user_model.objects.filter(
                is_staff=False,
                is_superuser=False,
                **kwargs,
            )
            .filter(Q(password__startswith=UNUSABLE_PASSWORD_PREFIX))
            .exclude(teacher__isnull=False)
            .first()
        )

        # find the user via email address, if it exists
        email = lti.user_email(request)
        if user is None and email:
            user = (
                user_model.objects.filter(
                    email=email,
                    is_staff=False,
                    is_superuser=False,
                )
                .filter(Q(password__startswith=UNUSABLE_PASSWORD_PREFIX))
                .exclude(teacher__isnull=False)
                .first()
            )

        if user is None:
            # find the user via hashed username
            username = self.get_hashed_username(request, lti)
            user = (
                user_model.objects.filter(
                    username=username,
                    is_staff=False,
                    is_superuser=False,
                )
                .filter(Q(password__startswith=UNUSABLE_PASSWORD_PREFIX))
                .exclude(teacher__isnull=False)
                .first()
            )

        return user


def manage_LTI_studentgroup(request):
    """
    based on parameters stored in session by django-lti-provider,
        - create StudentGroup
            - attach Teacher & Student
            - create InstitutionalLMS and InstitutionObject,
              attach to StudentGroup
            - assign year, semester and Discipline of teacher
              to StudentGroup
    """
    teacher_hash = request.session.get("custom_teacher_id", None)
    course_id = request.session.get("context_id", "")
    course_title = request.session.get("context_title", None)

    if not course_id:
        logout(request)
        raise LTIException()

    try:
        group = StudentGroup.objects.get(name=course_id)
    except StudentGroup.DoesNotExist:
        if course_title:
            group = StudentGroup(name=course_id, title=course_title)
        else:
            group = StudentGroup(name=course_id)
        group.semester = current_semester()
        group.year = current_year()
        group.mode_created = StudentGroup.LTI_STANDALONE
        group.save()

        if lms_url_raw := request.session.get(
            "launch_presentation_return_url", None
        ):
            lms_url = urlparse(lms_url_raw).hostname
            (
                institutional_lms,
                created,
            ) = InstitutionalLMS.objects.get_or_create(url=lms_url)
            if created:
                institution = Institution.objects.create(
                    name=institutional_lms.url
                )
                institutional_lms.institution = institution

            group.institution = institutional_lms.institution
            group.save()
        else:
            session_data = dict(request.session.items())
            logger.info("No LMS URL found in session data: {session_data}")

    # add group to student
    student = request.user.student
    if group not in student.groups.all():
        student.join_group(group=group)

    # If teacher_id specified, add teacher to group
    if teacher_hash is not None:
        teacher = Teacher.get(teacher_hash)
        if teacher not in group.teacher.all():
            group.teacher.add(teacher)
            teacher.current_groups.add(group)
            teacher.save()
