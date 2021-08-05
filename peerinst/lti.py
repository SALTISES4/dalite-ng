import base64
import hashlib
import logging

from django.contrib.auth import get_permission_codename, login
from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django_lti_tool_provider import AbstractApplicationHookManager

from peerinst.auth import authenticate_student

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
    LTI_KEYS = ["custom_assignment_id", "custom_question_id"]
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
        question_id = lti_data.get("custom_question_id")
        show_results_view = lti_data.get("custom_show_results_view", "false")

        if action == "launch-admin":
            return reverse("admin:index")
        elif action == "edit-question":
            return reverse(
                "admin:peerinst_question_change", args=(question_id,)
            )

        redirect_url = reverse(
            "question",
            kwargs=dict(assignment_id=assignment_id, question_id=question_id),
        )
        if show_results_view == "true":
            redirect_url += "?show_results_view=true"
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

        # Attaches login type to session to allow view access control via
        # middleware
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
        try:
            return ":".join(str(lti_data[k]) for k in self.LTI_KEYS)
        except KeyError:
            # D2L myCourses LTI POST request appends trailing "_" at end of
            # custom parameters
            _lti_data = {k.rstrip("_"): v for k, v in lti_data.items()}
            return ":".join(str(_lti_data[k]) for k in self.LTI_KEYS)

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
