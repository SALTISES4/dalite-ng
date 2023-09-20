from django.db.models import Exists, OuterRef, Q

from peerinst.models import Answer, AnswerChoice, Question
from REST.serializers import AnswerChoiceSerializer, QuestionSerializer
from REST.viewsets import TeacherCreateUpdateViewSet


class TeacherQuestionCreateUpdateViewSet(TeacherCreateUpdateViewSet):
    """
    Question create, retrieve and update for teacher

    - Attaches user on create via serializer
    - Validates editability before retrieve
    - Validates editability before update
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
        )
        queryset = queryset.filter(~Exists(answers))

        return queryset


class TeacherAnswerChoiceCreateUpdateViewSet(TeacherCreateUpdateViewSet):
    """
    AnswerChoice create, retrieve and update for teacher

    - Validates related question editability before retrieve
    - Validates related question editability before update
    """

    serializer_class = AnswerChoiceSerializer

    def get_queryset(self):
        """
        A user can only retrieve or update answer choices where
        they are either the owner or a collaborator of related question
        """
        queryset = AnswerChoice.objects.filter(
            Q(question__user=self.request.user)
            | Q(question__collaborators=self.request.user)
        )
        """
        And where there are no *student* answers for related question
        """
        answers = (
            Answer.objects.filter(question=OuterRef("question__pk"))
            .exclude(expert=True)
            .exclude(user_token__exact="")
        )
        queryset = queryset.filter(~Exists(answers))

        return queryset
