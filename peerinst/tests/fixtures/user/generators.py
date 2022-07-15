from django.contrib.auth.models import User

from peerinst.models import NewUserRequest, UserType, UserUrl


def new_users(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "username": f"user{i}",
                "email": f"test{i}@test.com",
                "password": "test",
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_users(users):
    users_ = [User.objects.create_user(**u) for u in users]
    for user in users_:
        if not hasattr(user, "url"):
            UserUrl.objects.create(user=user, url="test.com")
    return users_


def add_user_requests(users):
    for user in users:
        user.is_active = False
        user.save()
    return [
        NewUserRequest.objects.create(
            user=user, type=UserType.objects.get(type="teacher")
        )
        for user in users
    ]
