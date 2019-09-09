from django.contrib.auth.models import User


def new_users(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "username": "user{}".format(i),
                "email": "test{}@test.com".format(i),
                "password": "test",
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_users(users):
    return [User.objects.create_user(**u) for u in users]
