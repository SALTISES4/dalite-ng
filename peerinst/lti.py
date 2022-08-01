import logging
from urllib.parse import urlparse

from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission

from .models import Institution, InstitutionalLMS, StudentGroup, Teacher
from .models.group import current_semester, current_year

logger = logging.getLogger(__name__)


class LTIRoles:
    """
    Non-comprehensive list of roles commonly used in LTI applications
    """

    LEARNER = "Learner"
    INSTRUCTOR = "Instructor"
    STAFF = "Staff"


MODELS_STAFF_USER_CAN_EDIT = (
    ("peerinst", "question"),
    ("peerinst", "assignment"),
    ("peerinst", "category"),
)


def get_permissions_for_staff_user():
    """
    Returns all permissions that staff user possess. Staff user can create and
    edit all models from `MODELS_STAFF_USER_CAN_EDIT` list. By design he has no
    delete privileges --- as deleting questions could lead to bad user
    experience for students.

    :return: Iterable[django.contrib.auth.models.Permission]
    """
    from django.apps.registry import apps

    for app_label, model_name in MODELS_STAFF_USER_CAN_EDIT:
        model = apps.get_model(app_label, model_name)
        for action in ("add", "change"):
            codename = get_permission_codename(action, model._meta)
            yield Permission.objects.get_by_natural_key(
                codename, app_label, model_name
            )


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

        lms_url_raw = request.session.get(
            "launch_presentation_return_url", None
        )
        if lms_url_raw:
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
            session_data = {k: v for k, v in request.session.items()}
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
