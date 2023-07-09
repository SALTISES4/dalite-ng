from django.urls import include, path

from . import views as views_teacher

app_name = "teacher"

assignment_patterns = [
    path(
        "<str:identifier>/",
        views_teacher.AssignmentDetailView.as_view(),
        name="assignment-detail",
    ),
    path(
        "create/",
        views_teacher.AssignmentCreateView.as_view(),
        name="assignment-create",
    ),
    path(
        "update/<str:identifier>/",
        views_teacher.AssignmentUpdateView.as_view(),
        name="assignment-update",
    ),
]

urlpatterns = [
    path(
        "<int:pk>/",
        views_teacher.TeacherDashboardView.as_view(),
        name="dashboard",
    ),
    path(
        "<int:pk>/search/",
        views_teacher.SearchView.as_view(),
        name="search",
    ),
    path(
        "<int:pk>/library/",
        views_teacher.LibraryView.as_view(),
        name="library",
    ),
    path("<int:pk>/assignment/", include(assignment_patterns)),
]
