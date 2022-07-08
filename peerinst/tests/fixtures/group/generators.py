from peerinst.models import StudentGroup


def new_groups(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {"name": f"group{i}", "title": f"group{i}"}

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_groups(groups):
    groups = groups if hasattr(groups, "__iter__") else [groups]
    return [StudentGroup.objects.create(**g) for g in groups]
