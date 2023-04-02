from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.viewsets import ReadOnlyModelViewSet

from peerinst.models import Assignment, Collection, Question
from REST.permissions import IsTeacher
from REST.serializers import AssignmentSerializer, QuestionSerializer

from .views import CollectionViewSet


class TeacherLibraryAssignmentViewSet(ReadOnlyModelViewSet):
    """
    Owned and followed assignments
    - Bookmarking via TeacherView
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        followed_pks = self.request.user.teacher.assignments.values_list(
            "pk", flat=True
        )

        owned_pks = Assignment.objects.filter(
            owner=self.request.user
        ).values_list("pk", flat=True)

        pks = list(followed_pks) + [
            pk for pk in owned_pks if pk not in followed_pks
        ]

        return Assignment.objects.filter(pk__in=pks)


class TeacherLibraryCollectionViewSet(CollectionViewSet):
    """
    Owned and followed collections
    - Supports bookmarking through parent class
    """

    def get_queryset(self):
        # TODO: Update related name in Collection model?

        followed_pks = self.request.user.teacher.followers.values_list(
            "pk", flat=True
        )

        owned_pks = Collection.objects.filter(
            owner=self.request.user.teacher
        ).values_list("pk", flat=True)

        pks = list(followed_pks) + [
            pk for pk in owned_pks if pk not in followed_pks
        ]

        return Collection.objects.filter(pk__in=pks).order_by("-last_modified")


class TeacherLibraryQuestionViewSet(ReadOnlyModelViewSet):
    """
    Owned and followed questions
    - Bookmarking via TeacherView
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        followed_pks = (
            self.request.user.teacher.favourite_questions.values_list(
                "pk", flat=True
            )
        )

        owned_pks = Question.objects.filter(
            user=self.request.user
        ).values_list("pk", flat=True)

        pks = list(followed_pks) + [
            pk for pk in owned_pks if pk not in followed_pks
        ]

        return Question.objects.filter(pk__in=pks)
