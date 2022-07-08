from django.contrib.auth.models import User


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
    return [User.objects.create_user(**u) for u in users]
