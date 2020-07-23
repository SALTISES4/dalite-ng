import base64
import hashlib
import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_permission_codename, login
from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django_lti_tool_provider import AbstractApplicationHookManager
from django_lti_tool_provider.models import LtiUserData

from peerinst.auth import authenticate_student
from .students import create_student_token
from peerinst.models import (
    Assignment,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)
from .util import get_object_or_none

logger = logging.getLogger(__name__)


class LTIRoles(object):
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


class ApplicationHookManager(AbstractApplicationHookManager):
    LTI_KEYS = ["custom_assignment_id"]
    ADMIN_ACCESS_ROLES = {LTIRoles.INSTRUCTOR, LTIRoles.STAFF}

    @classmethod
    def _compress_user_name(cls, username):
        try:
            binary = username.encode()
        except TypeError:
            # We didn't get a normal edX hex user id, so we don't use our
            # custom encoding. This makes previewing questions in Studio work.
            return username
        else:
            return base64.urlsafe_b64encode(binary).decode().replace("=", "+")

    @classmethod
    def _generate_password(cls, base, nonce):
        # it is totally fine to use md5 here, as it only generates PLAIN STRING
        # password which is than fed into secure password hash
        generator = hashlib.md5()
        generator.update(base.encode())
        generator.update(nonce.encode())
        return generator.digest()

    def authenticated_redirect_to(self, request, lti_data):
        action = lti_data.get("custom_action")
        assignment_id = lti_data.get("custom_assignment_id")

        question_id = lti_data.get("custom_question_id", None)
        if (
            question_id is not None
            and "custom_question_id" not in self.LTI_KEYS
        ):
            self.LTI_KEYS.append("custom_question_id")
        student_group_assignment_id = lti_data.get(
            "custom_student_group_assignment_id", None
        )
        if (
            student_group_assignment_id is not None
            and "custom_student_group_assignment_id" not in self.LTI_KEYS
        ):
            self.LTI_KEYS.append("custom_student_group_assignment_id")

        show_results_view = lti_data.get("custom_show_results_view", "false")

        if action == "launch-admin":
            return reverse("admin:index")
        elif action == "edit-question":
            return reverse(
                "admin:peerinst_question_change", args=(question_id,)
            )
        elif question_id is None:
            if student_group_assignment_id is None:
                lti_user_data_object = get_object_or_none(
                    LtiUserData,
                    user=request.user,
                    custom_key=str(assignment_id)
                    + ":"
                    + str(
                        Assignment.objects.get(pk=assignment_id)
                        .questions.all()
                        .first()
                        .pk
                    ),
                )
                course_id = lti_user_data_object.edx_lti_parameters.get(
                    "context_id"
                )
                course_title = lti_user_data_object.edx_lti_parameters.get(
                    "context_title"
                )
                try:
                    group = StudentGroup.objects.get(name=course_id)
                except StudentGroup.DoesNotExist:
                    if course_title:
                        group = StudentGroup(
                            name=course_id, title=course_title
                        )
                    else:
                        group = StudentGroup(name=course_id)
                    group.save()
                teacher_hash = lti_user_data_object.edx_lti_parameters.get(
                    "custom_teacher_id"
                )
                if teacher_hash is not None:
                    teacher = Teacher.get(teacher_hash)
                    if teacher not in group.teacher.all():
                        group.teacher.add(teacher)
                        teacher.current_groups.add(group)
                        teacher.save()
                if hasattr(request.user, "student"):
                    request.user.student.groups.add(group)
                try:
                    student_group_assignment = StudentGroupAssignment.objects.get(
                        group=group,
                        assignment=Assignment.objects.get(pk=assignment_id),
                    )
                except StudentGroupAssignment.DoesNotExist:
                    student_group_assignment = StudentGroupAssignment.objects.create(
                        group=group,
                        assignment=Assignment.objects.get(pk=assignment_id),
                        distribution_date=datetime.now(),
                        due_date=datetime.now() + timedelta(days=365),
                    )

                return (
                    reverse(
                        "live",
                        kwargs=dict(
                            token=create_student_token(
                                request.user.username, request.user.email,
                            ),
                            assignment_hash=student_group_assignment.hash,
                        ),
                    )
                    + "&is_lti=true"
                )
            else:
                student_group_assignment = StudentGroupAssignment.objects.filter(
                    pk=student_group_assignment_id
                ).first()
                if hasattr(request.user, "student"):
                    request.user.student.groups.add(
                        student_group_assignment.group
                    )
                return (
                    reverse(
                        "live",
                        kwargs=dict(
                            token=create_student_token(
                                request.user.username, request.user.email,
                            ),
                            assignment_hash=student_group_assignment.hash,
                        ),
                    )
                    + "&is_lti=true"
                )

        redirect_url = reverse(
            "question",
            kwargs=dict(assignment_id=assignment_id, question_id=question_id),
        )

        if show_results_view == "true":
            if student_group_assignment_id is None:
                redirect_url += "?show_results_view=true"
            else:
                redirect_url += (
                    "?student_group_assignment_pk="
                    + str(student_group_assignment_id)
                    + "&show_results_view=true"
                )
        elif student_group_assignment_id is not None:
            redirect_url += "?student_group_assignment_pk=" + str(
                student_group_assignment_id
            )

        return redirect_url

    def authentication_hook(
        self,
        request,
        user_id=None,
        username=None,
        email=None,
        extra_params=None,
    ):
        if extra_params is None:
            extra_params = {}

        # username and email might be empty, depending on how edX LTI module
        # is configured:
        # there are individual settings for that + if it's embedded into an
        # iframe it never sends email and username in any case so, since we
        # want to track user for both iframe and non-iframe LTI blocks,
        # username is completely ignored

        email = email if email else user_id + "@localhost"

        user, __ = authenticate_student(request, email, user_id)

        if isinstance(user, User):
            login(
                request,
                user,
                backend="peerinst.backends.CustomPermissionsBackend",
            )

        # LTI sessions are created implicitly, and are not terminated when
        # user logs out of Studio/LMS, which may lead to granting access to
        # unauthorized users in shared computer setting. Students have no way
        # to terminate dalite session (other than cleaning cookies). This
        # setting instructs browser to clear session when browser is
        # closed --- this allows staff user to terminate the session easily,
        # which decreases the chance of session hijacking in shared computer
        # environment.

        # TL; DR; Sets session expiry on browser close.
        request.session.set_expiry(0)
        request.session["LTI"] = True

    def is_user_staff(self, extra_params):
        """
        Returns true if given circumstances user is considered as having a
        staff account.
        :param dict extra_params: Additional parameters passed by LTI.
        :return: bool
        """
        # SALTISE/S4 version has no staff users
        return False

    def update_staff_user(self, user):
        """
        Updates user to acknowledge he is a staff member
        :param django.contrib.auth.models.User user:
        :return: None
        """
        user.is_staff = True
        user.user_permissions.add(*get_permissions_for_staff_user())
        user.save()

    def vary_by_key(self, lti_data):
        question_id = lti_data.get("custom_question_id", None)
        if (
            question_id is not None
            and "custom_question_id" not in self.LTI_KEYS
        ):
            self.LTI_KEYS.append("custom_question_id")
        student_group_assignment_id = lti_data.get(
            "custom_student_group_assignment_id", None
        )
        if (
            student_group_assignment_id is not None
            and "custom_student_group_assignment_id" not in self.LTI_KEYS
        ):
            self.LTI_KEYS.append("custom_student_group_assignment_id")
        return ":".join(str(lti_data[k]) for k in self.LTI_KEYS)

    def optional_lti_parameters(self):
        """
        Return a dictionary of LTI parameters supported/required by this
        AuthenticationHookManager in addition to user_id, username and email.
        These parameters are passed to authentication_hook method via kwargs.

        This dictionary should have LTI parameter names (as specified by LTI
        specification) as keys; values are used as parameter names passed to
        authentication_hook method, i.e. it allows renaming (not always
        intuitive) LTI spec parameter names.

        Example:
            # renames lis_person_name_given -> user_first_name,
            # lis_person_name_family -> user_lat_name
            {'lis_person_name_given': 'user_first_name',
            'lis_person_name_family': 'user_lat_name'}
        """
        return {"roles": "roles"}
