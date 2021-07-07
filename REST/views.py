from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.viewsets import ReadOnlyModelViewSet

from peerinst.models import (
    Answer,
    AnswerAnnotation,
    Assignment,
    AssignmentQuestions,
    Discipline,
    Question,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)
from peerinst.util import question_search_function
from REST.pagination import SearchPagination
from REST.permissions import (
    InAssignmentOwnerList,
    InOwnerList,
    InTeacherList,
    IsAdminUserOrReadOnly,
    IsNotStudent,
    IsTeacher,
)
from REST.serializers import (
    AnswerSerializer,
    AssignmentSerializer,
    DisciplineSerializer,
    FeedbackReadSerialzer,
    FeedbackWriteSerialzer,
    QuestionSerializer,
    RankSerializer,
    StudentGroupAssignmentAnswerSerializer,
    StudentGroupSerializer,
    TeacherSerializer,
)


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing assignments and editing question order.
    """

    http_method_names = ["get", "patch"]
    permission_classes = [IsAuthenticated, InOwnerList]
    renderer_classes = [JSONRenderer]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(owner=self.request.user)


class DisciplineViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet to serve list of current disciplines.
    """

    permission_classes = [IsAuthenticated, IsNotStudent, IsAdminUserOrReadOnly]
    queryset = Discipline.objects.all()
    renderer_classes = [JSONRenderer]
    serializer_class = DisciplineSerializer


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for questions.

    TODO: Remove list option to reduce db load.
    """

    permission_classes = [IsAuthenticated, IsNotStudent]
    queryset = Question.objects.all()
    renderer_classes = [JSONRenderer]

    def get_serializer(self, *args, **kwargs):
        return QuestionSerializer(
            fields=["choices", "pk", "text", "title"], *args, **kwargs
        )


class QuestionListViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for adding and removing assignment questions.
    """

    http_method_names = ["delete", "get", "post"]
    serializer_class = RankSerializer
    permission_classes = [IsAuthenticated, IsNotStudent, InAssignmentOwnerList]

    def get_queryset(self):
        return AssignmentQuestions.objects.filter(
            assignment__owner=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        if self.get_object().assignment.editable:
            return super(QuestionListViewSet, self).destroy(
                request, *args, **kwargs
            )

        raise PermissionDenied


class QuestionSearchList(generics.ListAPIView):
    """A simple ListView to return search results in JSON format"""

    pagination_class = SearchPagination
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        assignment_id = self.request.GET.get("assignment_id")
        discipline = self.request.GET.get("discipline")
        search_string = self.request.GET.get("search_string")
        favourites_only = search_string == ""

        queryset = Question.objects.all()

        # Remove questions from this assignment
        if assignment_id:
            try:
                assignment = Assignment.objects.get(pk=assignment_id)
                queryset = queryset.exclude(pk__in=assignment.questions.all())
            except ObjectDoesNotExist:
                pass

        # Favourites only
        if favourites_only:
            queryset = queryset.filter(
                pk__in=self.request.user.teacher.favourite_questions.all()
            )
            return queryset

        if discipline:
            queryset = queryset.filter(discipline=discipline)

        # Call search function
        queryset = question_search_function(
            search_string, pre_filtered_list=queryset, is_old_query=True
        )

        return queryset

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return QuestionSerializer(
            read_only=True,
            fields=(
                "pk",
                "title",
                "text",
                "user",
                "difficulty",
                "discipline",
                "answer_count",
                "assignment_count",
                "answer_style",
                "category",
                "image",
                "image_alt_text",
                "choices",
                "matrix",
                "freq",
                "collaborators",
                "type",
                "peer_impact",
            ),
            *args,
            **kwargs,
        )


class StudentReviewList(generics.ListAPIView):
    """
    List all answers submitted by authenticated student, with associated
    question and most convincing rationales
    """

    serializer_class = AnswerSerializer

    def get_queryset(self):
        """
        return answers submitted by authenticated student
        """

        student = self.request.user
        return Answer.objects.filter(user_token=student.username)


class StudentFeedbackList(generics.ListAPIView):
    """
    List all Feedback (AnswerAnnotation objects) for
    authenticated student's answers
    """

    serializer_class = FeedbackReadSerialzer

    def get_queryset(self):
        return AnswerAnnotation.objects.filter(
            answer__user_token=self.request.user.username
        ).filter(Q(score__isnull=False) | Q(note__isnull=False))


class TeacherView(generics.RetrieveUpdateAPIView):
    """
    RU operations for teacher favourites
    """

    http_method_names = ["get", "put"]
    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = TeacherSerializer

    def get_queryset(self):
        return Teacher.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        current_favorites = (
            Teacher.objects.get(user=request.user)
            .favourite_questions.all()
            .values_list("pk", flat=True)
        )
        new_favorites = request.data["favourite_questions"]

        if len(current_favorites) - len(new_favorites) > 0:
            q_pk = list(set(current_favorites) - set(new_favorites))[0]
            message = f"#{q_pk} removed from favourites"
        else:
            q_pk = list(set(new_favorites) - set(current_favorites))[0]
            message = f"#{q_pk} added to favourites"

        snackbar_message = {"snackbar_message": message}

        response = super(TeacherView, self).update(request, *args, **kwargs)
        response.data.update(snackbar_message)

        return response


class TeacherFeedbackList(generics.ListCreateAPIView):
    """
    endpoint to list authenticated user's feedback given
    (AnswerAnnotation objects where they are annotator),
    or create new one
    """

    permission_classes = [IsAuthenticated, IsNotStudent]
    serializer_class = FeedbackWriteSerialzer

    def get_queryset(self):
        return AnswerAnnotation.objects.filter(
            annotator=self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(annotator=self.request.user)


class TeacherFeedbackDetail(generics.RetrieveUpdateAPIView):
    """
    View for RUD operations on AnswerAnnotation model
    """

    permission_classes = [IsAuthenticated, IsNotStudent]
    serializer_class = FeedbackWriteSerialzer

    def get_queryset(self):
        return AnswerAnnotation.objects.filter(
            annotator=self.request.user,
        )


class TeacherFeedbackThroughAnswerDetail(TeacherFeedbackDetail):
    """
    Same as above, but access instance through answer pk.
    This is a convenience and only works because of unique_together constraint.
    """

    def get_object(self):
        obj = get_object_or_404(
            AnswerAnnotation,
            annotator=self.request.user,
            answer__pk=self.kwargs["pk"],
        )
        self.check_object_permissions(self.request, obj)

        return obj


class TeacherSearch(ReadOnlyModelViewSet):

    permission_classes = [IsAuthenticated, IsTeacher]
    renderer_classes = [JSONRenderer]
    serializer_class = TeacherSerializer

    def get_queryset(self):
        """
        Return a list of Teacher instances that best match query, or None
        """
        query = self.request.query_params.get("query", None)
        if query is not None:
            return Teacher.objects.filter(
                user__is_active=True, user__username__startswith=query
            )
        return Teacher.objects.none()

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()

        return TeacherSerializer(
            read_only=True, fields=["pk", "user"], *args, **kwargs
        )


class StudentGroupUpdateView(generics.UpdateAPIView):
    """
    View to update list of teachers associated with a StudentGroup
    """

    permission_classes = [IsAuthenticated, IsTeacher, InTeacherList]
    renderer_classes = [JSONRenderer]
    serializer_class = StudentGroupSerializer

    def get_queryset(self):
        return StudentGroup.objects.filter(teacher=self.request.user.teacher)


class StudentGroupAssignmentAnswers(ReadOnlyModelViewSet):
    """
    View to list all student answers for
    - a given StudentGroup,
    - a given Question, and
    - a given Assignment

    Subject to the permissions requirements that
    - the User is authenticated,
    - the User is a Teacher, and
    - the Teacher is an owner of the StudentGroup

    Receives question_pk as url kwarg
    """

    permission_classes = [IsAuthenticated, IsTeacher, InTeacherList]
    renderer_classes = [JSONRenderer]
    serializer_class = StudentGroupAssignmentAnswerSerializer

    def get_queryset(self):
        """
        Limit queryset to this user's StudentGroups
        """
        return StudentGroupAssignment.objects.filter(
            group__teacher=self.request.user.teacher
        )

    def get_serializer_context(self):
        """
        Pass question pk to serializer
        """
        context = super().get_serializer_context()
        context.update(question_pk=self.kwargs.get("question_pk", None))
        return context
