from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from peerinst.models import Question
from REST.permissions import IsTeacher
from REST.serializers import QuestionSerializer


class TeacherQuestionRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        """
        Recommendations should be:
        - Discipline based: don't recommend Western Civ to Chemistry teachers
        - Popular: those with many answers or often used in assignments
        - Timely: change based on week of course

        Currently, returns newest in discipline.
        """
        queryset = Question.objects.exclude(user__isnull=True)

        if self.request.user.teacher.disciplines.count() > 0:
            queryset.filter(
                discipline__in=self.request.user.teacher.disciplines.all()
            )

        # Generate N valid questions from queryset
        def valid_questions(qs, n=4):
            count = 0
            for q in qs:
                if q.is_valid:
                    yield q
                    count += 1
                    if count >= n:
                        break

        return valid_questions(queryset)
