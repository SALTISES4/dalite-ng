from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from peerinst.documents import TeacherDocument
from peerinst.models import Teacher
from REST.backends import ORMBackupBaseDocumentViewSet
from REST.filters import UsernameWildcardFilter
from REST.permissions import IsTeacher
from REST.serializers import TeacherSearchSerializer


class TeacherViewSet(ORMBackupBaseDocumentViewSet):
    """
    Searchable read-only endpoint for teacher usernames.

    Supports retrieve, list and ?username__wildcard filtering.

    TODO: Limit objects returned from DRF List
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = TeacherSearchSerializer

    # DRF/django-filter
    lookup_field = "user__username"
    filterset_class = UsernameWildcardFilter
    queryset = Teacher.objects.all()

    # DRF/DSL
    document = TeacherDocument
    document_uid_field = "id"
    filter_fields = {
        "username": "username",
    }
    lookup_url_kwarg = "id"
    pagination_class = None
