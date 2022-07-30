from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied
from lti_provider.auth import LTIBackend


class CustomPermissionsBackend(ModelBackend):
    """A custom auth backend to validate object-level permissions."""

    def has_perm(self, user_obj, perm, obj=None):

        if not obj:
            return super().has_perm(user_obj, perm)
        try:
            # Assumes ownership is defined by user OneToOneField or collaborators ManyToManyField
            if user_obj == obj.user or user_obj in obj.collaborators.all():
                # Has permission for _this_ object; proceed with normal permissions check
                return super().has_perm(user_obj, perm)
            else:
                # Prevent any further authentication checks
                raise PermissionDenied
        except Exception as e:
            if user_obj.is_staff:
                return super().has_perm(user_obj, perm)
            else:
                raise PermissionDenied from e


class DaliteLTIBackend(LTIBackend):
    """
    Extend django-lti-provider backend by adding the session variable `LTI`
    which serves as hint in templates for context
    """

    def authenticate(self, request, lti):
        request.session["LTI"] = True
        super().authenticate(request, lti)
