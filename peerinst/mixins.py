from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

from .models import Student, Teacher
from tos.models import Consent


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


def student_check(user):
    try:
        if user.teacher:
            # Let through Teachers unconditionally
            return True
    except:
        try:
            if user.student:
                return False
        except:
            # Allow through all non-Students, i.e. "guests"
            return True

class NoStudentsMixin(object):
    """A simple mixin to explicitly allow Teacher but prevent Student access to a view."""
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(NoStudentsMixin, cls).as_view(**initkwargs)
        return user_passes_test(student_check, login_url='/access_denied_and_logout/')(view)


class ObjectPermissionMixin(object):
    """Check object-level permissions."""
    def dispatch(self, *args, **kwargs):
        try:
            obj = self.get_object()
        except:
            obj = None
        if self.request.user.has_perm(self.object_permission_required, obj):
            return super(ObjectPermissionMixin, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied


def teacher_tos_accepted_check(user):
    return Consent.get(user.username, "teacher")

class TOSAcceptanceRequiredMixin(object):
    """Insist that TOS is accepted in order to access view."""
    """Used to protect views with content creation that requires license."""
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(TOSAcceptanceRequiredMixin, cls).as_view(**initkwargs)
        return user_passes_test(teacher_tos_accepted_check, login_url='/tos/required/')(view)
