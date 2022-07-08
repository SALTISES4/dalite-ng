import random

from django.contrib.contenttypes.models import ContentType
from pinax.forums.models import (
    Forum,
    ForumReply,
    ForumThread,
    ThreadSubscription,
)

from peerinst.models import TeacherNotification


def new_forum():
    return {"title": "test", "description": "test"}


def new_threads(n, forum, teachers, n_messages):
    def generator():
        i = 0
        while True:
            i += 1

            yield {
                "title": f"test{i}",
                "author": random.choice(teachers).user,
                "content": "test",
                "content_html": "test",
                "forum": forum,
                "posts": [
                    {
                        "author": random.choice(teachers).user,
                        "content": "test",
                        "content_html": "test",
                    }
                    for _ in range(n_messages)
                ],
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_forum(forum):
    return Forum.objects.create(**forum)


def add_threads(threads, teachers):
    notification_type = ContentType.objects.get(
        app_label="pinax_forums", model="ThreadSubscription"
    )
    threads_ = [
        ForumThread.objects.create(
            title=t["title"],
            forum=t["forum"],
            author=t["author"],
            content=t["content"],
            content_html=t["content_html"],
        )
        for t in threads
    ]
    for thread in threads_:
        for teacher in teachers:
            ThreadSubscription.objects.create(
                thread=thread, user=teacher.user, kind="thread"
            )

    for t, t_ in zip(threads, threads_):
        for post in t["posts"]:
            ForumReply.objects.create(
                author=post["author"],
                content=post["content"],
                content_html=post["content_html"],
                thread=t_,
            )
            for subscription in ThreadSubscription.objects.filter(
                thread=thread
            ):
                TeacherNotification.objects.get_or_create(
                    teacher=teacher,
                    notification_type=notification_type,
                    object_id=subscription.id,
                )
    return threads_
