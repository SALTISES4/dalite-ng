from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from peerinst.models import Assignment, Question
from REST.permissions import IsTeacher
from REST.serializers import AssignmentSerializer, QuestionSerializer


class TeacherAssignmentRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        """
        Recommendations should be:
        - Discipline based: don't recommend Western Civ to Chemistry teachers
        - Popular: those with many answers or often used in assignments
        - Timely: change based on week of course
        - Not your own

        Currently, returns newest.
        """
        queryset = (
            Assignment.objects.all()
            .exclude(owner=self.request.user)
            .exclude(pk__in=self.request.user.teacher.assignments.all())
            .order_by("-created_on")
        )

        # Generate N valid assignments from queryset
        def valid_assignments(qs, n=4):
            count = 0
            for a in qs:
                if a.is_valid:
                    yield a
                    count += 1
                    if count >= n:
                        break

        return valid_assignments(queryset)


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
        - Not your own

        Currently, returns newest in discipline.
        """
        queryset = (
            Question.objects.exclude(user__isnull=True)
            .exclude(user=self.request.user)
            .exclude(collaborators=self.request.user)
            .exclude(
                pk__in=self.request.user.teacher.favourite_questions.all()
            )
            .order_by("-created_on")
        )

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
