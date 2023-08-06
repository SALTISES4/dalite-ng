from django.urls import include, path

from . import views

app_name = "teacher"

assignment_patterns = [
    path(
        "create/",
        views.AssignmentCreateView.as_view(),
        name="assignment-create",
    ),
    path(
        "update/<str:identifier>/",
        views.AssignmentUpdateView.as_view(),
        name="assignment-update",
    ),
    path(
        "view/<str:identifier>/",
        views.AssignmentDetailView.as_view(),
        name="assignment-detail",
    ),
]

question_patterns = [
    path(
        "create/",
        views.QuestionCreateView.as_view(),
        name="question-create",
    ),
]

urlpatterns = [
    path(
        "<int:pk>/",
        views.DashboardView.as_view(),
        name="dashboard",
    ),
    path(
        "<int:pk>/library/",
        views.LibraryView.as_view(),
        name="library",
    ),
    path("assignment/", include(assignment_patterns)),
    path("question/", include(question_patterns)),
    path(
        "search/",
        views.SearchView.as_view(),
        name="search",
    ),
]
