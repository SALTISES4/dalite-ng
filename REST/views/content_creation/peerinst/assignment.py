from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response

from peerinst.models import Assignment, Question
from REST.serializers import AssignmentSerializer
from REST.viewsets import TeacherCRUDViewSet


class TeacherAssignmentCRUDViewSet(TeacherCRUDViewSet):
    """
    Assignment create, retrieve, update and delete for teacher.

    - Attaches user on create via serializer
    - Teacher can only access their own content
    - Validates editability before update or delete
    """

    lookup_field = "identifier"
    lookup_value_regex = "[-a-zA-Z0-9_\.\s]+"
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        """
        Queryset returns objs that are editable but not necessarily deletable.

        - Explicitly check this object is deletable
        """
        if not instance.is_deletable:
            raise serializers.ValidationError(instance.delete_validation_error)
        instance.delete()

    @action(
        detail=True,
        methods=["post"],
        url_path="copy",
    )
    def copy(self, request, pk):
        assignment_to_copy = get_object_or_404(Assignment, pk=pk)
        if identifier := request.data.get("identifier"):
            serializer = AssignmentSerializer(
                data={
                    "pk": identifier,
                    "title": assignment_to_copy.title,
                    "description": assignment_to_copy.description,
                    "intro_page": assignment_to_copy.intro_page,
                    "conclusion_page": assignment_to_copy.conclusion_page,
                    "parent": assignment_to_copy,
                },
                context={"request": request},
            )
            if serializer.is_valid(raise_exception=True):
                new_assignment = serializer.save()
                # Add questions
                new_assignment.questions.set(
                    assignment_to_copy.questions.all()
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        else:
            raise serializers.ValidationError(_("Identifier missing"))

    @action(
        detail=False,
        methods=["get"],
        url_path="addable-for-question/(?P<question_pk>[0-9]+)",
    )
    def for_question(self, request, question_pk=None):
        # Return assignments to which given question can be added for teacher
        question = get_object_or_404(Question, pk=question_pk)
        queryset = self.get_queryset().exclude(questions=question)
        pks = [a.pk for a in queryset if a.is_editable]
        serializer = self.get_serializer(
            queryset.filter(pk__in=pks), many=True, fields=["pk", "title"]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
