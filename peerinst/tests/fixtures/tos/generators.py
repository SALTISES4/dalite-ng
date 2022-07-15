from tos.models import Consent as TosConsent
from tos.models import Role, Tos


def new_tos(n_of_each, roles):
    if isinstance(roles, str):
        roles = [roles]
    tos = []
    for role in roles:
        role_, __ = Role.objects.get_or_create(role=role)

        def generator():
            i = 0
            while True:
                i += 1
                yield {
                    "role": role_,
                    "version": i,
                    "text": f"tos{i}",
                    "current": False,
                }

        gen = generator()
        tos = tos + [next(gen) for _ in range(n_of_each)]
    return tos


def add_tos(tos_):
    tos_ = tos_ if hasattr(tos_, "__iter__") else [tos_]
    tos = [Tos.objects.create(**t) for t in tos_]
    current_idx = [
        max(i for i, t in enumerate(tos) if t.role == role and t.current)
        for role in {t.role for t in tos}
    ]
    for i, t in enumerate(tos):
        if i not in current_idx:
            t.current = False
    return tos


def new_tos_consents(users, toss):
    users = users if hasattr(users, "__iter__") else [users]
    toss = toss if hasattr(toss, "__iter__") else [toss]
    return [
        {"user": user, "tos": tos, "accepted": True}
        for user in users
        for tos in toss
    ]


def add_tos_consents(consents):
    consents = consents if hasattr(consents, "__iter__") else [consents]
    return [TosConsent.objects.create(**c) for c in consents]
