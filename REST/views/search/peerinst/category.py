from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from peerinst.documents import CategoryDocument
from peerinst.models import Category
from REST.backends import ORMBackupBaseDocumentViewSet
from REST.filters import TitleWildcardFilter
from REST.permissions import IsTeacher
from REST.serializers import CategorySerializer


class CategoryViewSet(ORMBackupBaseDocumentViewSet):
    """
    Searchable read-only endpoint for categories.

    Supports retrieve, list and ?title__wildcard filtering.
    """

    lookup_field = "title"
    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = CategorySerializer

    # DRF/django-filter
    filterset_class = TitleWildcardFilter
    queryset = Category.objects.all()

    # DRF/DSL
    document = CategoryDocument
    document_uid_field = "title"
    filter_fields = {"title": "title.raw"}
    lookup_url_kwarg = "title"
    pagination_class = None
