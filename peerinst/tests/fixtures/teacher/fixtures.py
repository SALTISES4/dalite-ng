import pytest

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from pinax.forums.models import ForumReply, ForumThread

from ..tos import consent_to_tos, tos_teacher  # noqa
from .generators import add_teachers, new_teachers


@pytest.fixture
def teacher(tos_teacher):
    teacher = add_teachers(new_teachers(1))[0]
    forum_thread_type = ContentType.objects.get_for_model(ForumThread)
    forum_reply_type = ContentType.objects.get_for_model(ForumReply)
    teacher.user.is_active = True
    teacher.user.save()
    teacher.user.user_permissions.add(
        Permission.objects.get(codename="add_question"),
        Permission.objects.get(codename="change_question"),
        Permission.objects.get(
            codename="add_forumthread", content_type=forum_thread_type
        ),
        Permission.objects.get(
            codename="add_forumreply", content_type=forum_reply_type
        ),
    )
    consent_to_tos(teacher, tos_teacher)
    return teacher


@pytest.fixture
def teachers(tos_teacher):
    teachers = add_teachers(new_teachers(5))
    forum_thread_type = ContentType.objects.get_for_model(ForumThread)
    forum_reply_type = ContentType.objects.get_for_model(ForumReply)
    for teacher in teachers:
        teacher.user.is_active = True
        teacher.user.save()
        teacher.user.user_permissions.add(
            Permission.objects.get(codename="add_question"),
            Permission.objects.get(codename="change_question"),
            Permission.objects.get(
                codename="add_forumthread", content_type=forum_thread_type
            ),
            Permission.objects.get(
                codename="add_forumreply", content_type=forum_reply_type
            ),
        )
        consent_to_tos(teacher, tos_teacher)
    return teachers
