from django_elasticsearch_dsl_drf.filter_backends import FilteringFilterBackend
from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet
from django_filters import rest_framework as filters
from rest_framework.viewsets import ReadOnlyModelViewSet


class ORMBackupBaseDocumentViewSet(BaseDocumentViewSet):
    """
    Check for Elastic connection and, if not available, default
    to a Django ORM search.
    """

    elastic = None
    filter_backends = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.client.ping():
            # Elasticsearch is available; set up DSL-DRF filtering
            self.elastic = True
            self.filter_backends = (FilteringFilterBackend,)
        else:
            # Elasticsearch is unavailable; set up ORM filtering
            self.elastic = False
            self.filter_backends = (filters.DjangoFilterBackend,)

    def get_object(self):
        if self.elastic:
            return super().get_object()
        return ReadOnlyModelViewSet.get_object(self)

    def get_queryset(self):
        if self.elastic:
            return super().get_queryset()
        return self.queryset or self.document.Django.model.objects.all()
