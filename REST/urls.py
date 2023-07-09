from django.urls import include, path
from rest_framework.routers import DefaultRouter

from REST import form_helpers, views

app_name = "REST"

peerinst_api = DefaultRouter()
peerinst_api.register(
    r"assignments", views.AssignmentViewSet, basename="assignment"
)
peerinst_api.register(
    r"disciplines",
    views.DisciplineViewSet,
    basename="discipline",
)
peerinst_api.register(
    r"assignment-questions",
    views.QuestionListViewSet,
    basename="assignment_question",
)
peerinst_api.register(
    r"questions",
    views.QuestionViewSet,
    basename="question",
)
peerinst_api.register(
    r"recommended-assignments",
    views.TeacherAssignmentRecommendationViewSet,
    basename="recommended-assignments",
)
peerinst_api.register(
    r"recommended-collections",
    views.TeacherCollectionRecommendationViewSet,
    basename="recommended-collections",
)
peerinst_api.register(
    r"recommended-questions",
    views.TeacherQuestionRecommendationViewSet,
    basename="recommended-questions",
)
peerinst_api.register(
    r"studentgroupassignments/recent",
    views.RecentStudentGroupAssignmentViewSet,
    basename="recent-studentgroupassignment",
)
peerinst_api.register(
    r"studentgroupassignments",
    views.StudentGroupAssignmentViewSet,
    basename="studentgroupassignment",
),
peerinst_api.register(
    r"collections",
    views.CollectionViewSet,
    basename="collection",
)
peerinst_api.register(
    r"teacher/library/assignments",
    views.TeacherLibraryAssignmentViewSet,
    basename="teacher-library-assignment",
)
peerinst_api.register(
    r"teacher/library/collections",
    views.TeacherLibraryCollectionViewSet,
    basename="teacher-library-collection",
)
peerinst_api.register(
    r"teacher/library/questions",
    views.TeacherLibraryQuestionViewSet,
    basename="teacher-library-question",
)

urlpatterns = [
    path("peerinst/", include(peerinst_api.urls)),
    path(
        "search/questions/",
        views.QuestionSearchList.as_view(),
        name="question-search",
    ),
    path(
        "student/review/",
        views.StudentReviewList.as_view(),
        name="student-review",
    ),
    path(
        "student/feedback/",
        views.StudentFeedbackList.as_view(),
        name="student-feedback",
    ),
    path(
        "studentgroup/update/<int:pk>/",
        views.StudentGroupUpdateView.as_view(),
        name="student-group-update",
    ),
    path(
        "studentgroupassignment/",
        views.StudentGroupAssignmentAnswers.as_view({"get": "list"}),
        name="student-group-assigment-answers",
    ),
    path(
        "studentgroupassignment/<int:pk>/<int:question_pk>/",
        views.StudentGroupAssignmentAnswers.as_view({"get": "retrieve"}),
        name="student-group-assigment-answers",
    ),
    path(
        "teacher/<int:pk>/",
        views.TeacherView.as_view(),
        name="teacher",
    ),
    path(
        "teacher/search/",
        views.TeacherSearch.as_view({"get": "list"}),
        name="teacher-search",
    ),
    path(
        "teacher/feedback/",
        views.TeacherFeedbackList.as_view(),
        name="teacher-feedback-list",
    ),
    path(
        "teacher/feedback/<int:pk>/",
        views.TeacherFeedbackDetail.as_view(),
        name="teacher-feedback-detail",
    ),
    path(
        "teacher/feedback/through_answer/<int:pk>/",
        views.TeacherFeedbackThroughAnswerDetail.as_view(),
        name="teacher-feedback-through-answer-detail",
    ),
    # Form helpers
    path(
        "form-helpers/assignment/check-id/",
        form_helpers.check_assignment_id_is_valid,
        name="assignment-check-id",
    ),
    path(
        "form-helpers/assignment/help-texts/",
        form_helpers.get_assignment_help_texts,
        name="assignment-help-texts",
    ),
]
