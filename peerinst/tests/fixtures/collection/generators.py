from peerinst.models import Collection


def new_collections(n, assignments, discipline, teachers):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "title": f"collection{i}",
                "description": "text",
                "discipline": discipline,
                "owner": teachers[0],
                "followers": teachers[1:],
                "assignments": assignments,
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_collections(collections):
    collections_ = []
    for collection in collections:
        collection_ = Collection.objects.create(
            title=collection["title"],
            description=collection["description"],
            discipline=collection["discipline"],
            owner=collection["owner"],
        )
        collection_.assignments.add(*collection["assignments"])
        collection_.followers.add(*collection["followers"])
        collections_.append(collection_)
    return collections_
