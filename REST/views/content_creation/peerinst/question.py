from rest_framework import serializers

from peerinst.models import Question
from REST.serializers import QuestionSerializer
from REST.viewsets import TeacherCRUDViewSet


class TeacherQuestionCRUDViewSet(TeacherCRUDViewSet):
    """
    Question create, retrieve, update and delete for teacher

    - Attaches user on create via serializer √
    - Teacher can only access their own content √
    - Validates editability before retrieve, update, or delete √
    """

    serializer_class = QuestionSerializer

    def get_queryset(self):
        return Question.editable_queryset_for_user(self.request.user)

    def perform_destroy(self, instance):
        """
        Queryset returns objects that are editable but not necessarily deletable
        - Explicitly check if this object is deletable
        """
        if not instance.is_deletable:
            raise serializers.ValidationError(instance.delete_validation_error)
        instance.delete()
