from django.contrib.auth.models import User

from peerinst.models import Teacher


def new_teachers(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "username": "teacher{}".format(i),
                "email": "test{}@test.com".format(i),
                "password": "test",
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_teachers(teachers):
    teachers = teachers if hasattr(teachers, "__iter__") else [teachers]
    users = []
    for teacher in teachers:
        try:
            users.append(User.objects.get(username=teacher["username"]))
        except User.DoesNotExist:
            users.append(User.objects.create_user(**teacher))
    return [Teacher.objects.get_or_create(user=user)[0] for user in users]
