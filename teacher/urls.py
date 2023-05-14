from django.urls import path

from . import views as views_teacher

app_name = "teacher"

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
    path(
        "<int:pk>/assignment/create/",
        views_teacher.AssignmentCreateView.as_view(),
        name="assignment-create",
    ),
]
