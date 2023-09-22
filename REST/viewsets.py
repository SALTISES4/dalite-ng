from rest_framework.mixins import (
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.viewsets import GenericViewSet

from REST.permissions import IsTeacher


class TeacherCreateUpdateViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    """
    - No list √
    - No PUT √
    - No DELETE √
    - Login required √
    - Teacher required √

    TODO: Consider if we need a TOS check
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post", "patch"]
