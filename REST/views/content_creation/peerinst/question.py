from django.db.models import Exists, OuterRef, Q

from peerinst.models import Answer, Question
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
        """
        A user can only retrieve or update questions where
        they are either the owner or a collaborator
        """
        queryset = Question.objects.filter(
            Q(user=self.request.user) | Q(collaborators=self.request.user)
        )
        """
        And where there are no *student* answers
        """
        answers = (
            Answer.objects.filter(question=OuterRef("pk"))
            .exclude(expert=True)
            .exclude(user_token__exact="")
            .exclude(user_token__exact=OuterRef("user__username"))
        )
        """
        TODO: And where no other teachers have assigned this question?
        """
        queryset = queryset.filter(~Exists(answers)).distinct()

        return queryset
