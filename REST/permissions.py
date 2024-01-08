from django.utils.translation import gettext_lazy as _
from rest_framework import permissions

from tos.models import Consent


class InOwnerList(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access/edit.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named `owner`.
        return request.user in obj.owner.all()


class InAssignmentOwnerList(permissions.BasePermission):
    """
    FIXME: Unused???
    Object-level permission to only allow owners of an object to access/edit.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named `owner`.
        return request.user in obj.assignment.owner.all()


class InTeacherList(permissions.BasePermission):
    """
    Object-level permission to only allow teachers to access a StudentGroup.

    To be used with IsTeacher view-level permission.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named `group` and `group` must have
        # attribute named `teacher` or instance must have `teacher`
        if hasattr(obj, "group") and hasattr(obj.group, "teacher"):
            return request.user.teacher in obj.group.teacher.all()
        elif hasattr(obj, "teacher"):
            return request.user.teacher in obj.teacher.all()
        raise AttributeError(
            "This object-level permission can only be applied against \
            models with a group attribute containing a list of teachers"
        )


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """GET only access for non-staff users."""

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS
            or request.user
            and request.user.is_staff
        )


class IsNotStudent(permissions.BasePermission):
    """User must not be a Student."""

    def has_permission(self, request, view):
        return not hasattr(request.user, "student")


class IsTeacher(permissions.BasePermission):
    """User must be a Teacher."""

    def has_permission(self, request, view):
        return hasattr(request.user, "teacher")


class IsTeacherWithTOSAccepted(permissions.BasePermission):
    """User must be a Teacher and have accepted latest TOS."""

    message = _(
        "Content creation requires a Teacher account and accepting the Terms of Service"  # noqa E501
    )

    def has_permission(self, request, view):
        if request.method.upper() in ["POST", "PATCH"]:
            return hasattr(request.user, "teacher") and Consent.get(
                request.user.username, "teacher"
            )

        return hasattr(request.user, "teacher")
