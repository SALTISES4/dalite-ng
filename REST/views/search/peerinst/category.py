from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from peerinst.documents import CategoryDocument
from peerinst.models import Category
from REST.backends import ORMBackupBaseDocumentViewSet
from REST.filters import WildcardFilter
from REST.permissions import IsTeacher
from REST.serializers import CategorySerializer


class CategoryViewSet(ORMBackupBaseDocumentViewSet):
    """
    Searchable read-only endpoint for categories.

    Supports retrieve, list and ?title__wildcard filtering.
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = CategorySerializer

    # DRF/django-filter
    lookup_field = "title"
    filterset_class = WildcardFilter
    queryset = Category.objects.all()

    # Link between approaches
    dsl_orm_filter_map = {"title": "title"}

    # DRF/DSL
    document = CategoryDocument
    document_uid_field = "title"
    filter_fields = {"title": "title.raw"}
    lookup_url_kwarg = "title"
    nested_filter_fields = {}
    pagination_class = None
