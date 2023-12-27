import pytest
from django.contrib.auth.models import Permission

from ..tos import consent_to_tos
from .generators import add_teachers, new_teachers


@pytest.fixture
def teacher(tos_teacher):
    teacher = add_teachers(new_teachers(1))[0]
    teacher.user.is_active = True
    teacher.user.save()
    teacher.user.user_permissions.add(
        Permission.objects.get(codename="add_question"),
        Permission.objects.get(codename="change_question"),
        Permission.objects.get(codename="delete_question"),
    )
    consent_to_tos(teacher, tos_teacher)
    return teacher


@pytest.fixture
def teachers(tos_teacher):
    teachers = add_teachers(new_teachers(5))
    for teacher in teachers:
        teacher.user.is_active = True
        teacher.user.save()
        teacher.user.user_permissions.add(
            Permission.objects.get(codename="add_question"),
            Permission.objects.get(codename="change_question"),
            Permission.objects.get(codename="delete_question"),
        )
        consent_to_tos(teacher, tos_teacher)
    return teachers
