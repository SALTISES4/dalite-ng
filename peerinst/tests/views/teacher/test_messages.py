import json

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from pinax.forums.models import ForumThread

from peerinst.models import TeacherNotification
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_messages(client, teacher, thread):
    assert login_teacher(client, teacher)

    notification_type = ContentType.objects.get(
        app_label="pinax_forums", model="ThreadSubscription"
    )

    resp = client.get(reverse("teacher-dashboard--messages"))
    assert resp.status_code == 200
    data = json.loads(resp.content)["threads"]

    assert len(data) == 1
    for thread in data:
        assert "id" in thread
        assert "last_reply" in thread
        assert "author" in thread["last_reply"]
        assert "content" in thread["last_reply"]
        assert (
            thread["n_new"]
            == TeacherNotification.objects.filter(
                teacher=teacher,
                notification_type=notification_type,
                object_id__in=ForumThread.objects.get(
                    id=thread["id"]
                ).subscriptions.values_list("id"),
            ).count()
        )

        resp = client.get(thread["link"])
        assert resp.status_code == 200
        assert "pinax/forums/thread.html" in resp.template_name
