from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import (
    DjangoModelPermissions,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.viewsets import GenericViewSet

from REST.permissions import IsTeacherWithTOSAccepted


class TeacherCRUDViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    """
    Generic base viewset for teacher-related models.

    - No list √
    - No PUT √
    - Login required √
    - Teacher required √
    - TOS required for create and update applied on child views √
    """

    permission_classes = [
        IsAuthenticated,
        IsTeacherWithTOSAccepted,
        DjangoModelPermissions,
    ]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch", "delete"]
