from django.urls import path

from . import views as views_teacher

app_name = "teacher"

urlpatterns = [
    path(
        "<int:pk>/",
        views_teacher.RedesignedTeacherDetailView.as_view(),
        name="dashboard",
    ),
]
