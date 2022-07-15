import random
import string

from django.contrib.auth.models import User

from tos.models import Consent as TosConsent
from tos.models import EmailConsent, EmailType, Role, Tos


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


def new_roles(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {"role": f"r{string.ascii_lowercase[i]}"}

    gen = generator()

    return [next(gen) for _ in range(n)]


def new_tos(n, roles, all_roles_present=False, random_current=True):
    def generator(roles):
        roles = [roles] if isinstance(roles, Role) else roles
        versions = {role: 0 for role in roles}
        gens = {role: 0 for role in roles}
        while True:
            role = random.choice(roles)
            tos = {
                "role": role,
                "version": versions[role],
                "text": f"text{gens[role]}",
                "current": False,
            }
            yield tos
            versions[role] += 1
            gens[role] += 1

    if all_roles_present:
        if n < len(roles):
            raise RuntimeError(
                "There aren't enough tos for all possible roles"
            )
        n_per_role = n // len(roles)
        gens = [generator([role]) for role in roles]
        tos = []
        for gen in gens:
            tos += [next(gen) for _ in range(n_per_role)]
        if len(tos) < n:
            tos += [next(random.choice(gens)) for _ in range(n - len(tos))]
    else:
        gen = generator(roles)
        tos = [next(gen) for _ in range(n)]

    if random_current:
        for role in {t["role"] for t in tos}:
            idx = [i for i, t in enumerate(tos) if t["role"] == role]
            tos[random.choice(idx)]["current"] = True

    return tos


def new_tos_consents(n, users, toss, all_combinations_present=False):
    def generator(users, toss):
        users = [users] if isinstance(users, User) else users
        toss = [toss] if isinstance(toss, Tos) else toss
        while True:
            user = random.choice(users)
            tos = random.choice(toss)
            yield {"user": user, "tos": tos, "accepted": random.random() > 0.5}

    if all_combinations_present:
        if n < len(users) * len(toss):
            raise RuntimeError(
                "There aren't enough consents for all possible users and tos"
            )
        n_per_combination = n // (len(users) * len(toss))
        gens = [generator([u], [t]) for u in users for t in toss]
        consents = []
        for gen in gens:
            consents += [next(gen) for _ in range(n_per_combination)]
        if len(consents) != n:
            consents += [
                next(random.choice(gens)) for _ in range(n - len(consents))
            ]
    else:
        gen = generator(users, toss)
        consents = [next(gen) for _ in range(n)]

    return consents


def new_email_types(
    n_per_role, roles, type_for_every_role=False, n_overlapping_types=0
):
    roles = [roles] if isinstance(roles, Role) else roles

    def generator(role):
        i = 0
        while True:
            i += 1
            yield {
                "role": role,
                "type": f"type{i}",
                "title": f"title{i}",
                "description": f"description{i}",
            }

    gen = generator(roles[0])
    types = [next(gen) for _ in range(n_per_role)]
    if type_for_every_role:
        for role in roles[1:]:
            types += [
                {
                    f: (role if f == "role" else v)
                    for f, v in list(elem.items())
                }
                for elem in types[:n_per_role]
            ]
    elif n_overlapping_types > 0:
        for role in roles[1:]:
            gen = generator(role)
            types += [
                {
                    f: (role if f == "role" else v)
                    for f, v in list(elem.items())
                }
                for elem in random.sample(
                    types[:n_per_role], k=n_overlapping_types
                )
            ] + [next(gen) for _ in range(n_per_role - n_overlapping_types)]
    else:
        for role in roles[1:]:
            gen = generator(role)
            types += [next(gen) for _ in range(n_per_role)]
    return types


def new_email_consents(n, users, email_types, all_combinations_present=False):
    if all_combinations_present and n < len(email_types) * len(users):
        raise ValueError("Not enough consents for all email types")

    users = [users] if isinstance(users, User) else users
    email_types = (
        [email_types] if isinstance(email_types, EmailType) else email_types
    )

    def generator(users, email_types):
        while True:
            yield {
                "user": random.choice(users),
                "email_type": random.choice(email_types),
                "accepted": random.random() > 0.5,
            }

    if all_combinations_present:
        n_per_type = n // (len(email_types) * len(users))
        gens = [generator([u], [t]) for t in email_types for u in users]
        consents = []
        for gen in gens:
            consents += [next(gen) for _ in range(n_per_type)]
        if n > len(consents):
            consents += [
                next(random.choice(gens)) for _ in range(n - len(consents))
            ]
    else:
        gen = generator(users, email_types)
        consents = [next(gen) for _ in range(n)]
    return consents


def add_users(users):
    return [User.objects.create_user(**u) for u in users]


def add_roles(roles):
    return [Role.objects.create(**r) for r in roles]


def add_tos(tos_):
    tos = [Tos.objects.create(**t) for t in tos_]
    current_idx = [
        max(i for i, t in enumerate(tos) if t.role == role and t.current)
        for role in {t.role for t in tos}
    ]
    for i, t in enumerate(tos):
        if i not in current_idx:
            t.current = False
    return tos


def add_tos_consents(consents):
    return [TosConsent.objects.create(**c) for c in consents]


def add_email_types(email_types):
    return [EmailType.objects.create(**t) for t in email_types]


def add_email_consents(consents):
    return [EmailConsent.objects.create(**c) for c in consents]


def _extra_chars_gen():
    letters = string.ascii_letters
    indices = [0]
    while True:
        yield "".join(letters[i] for i in indices)
        for i in range(len(indices)):
            if indices[i] < len(letters) - 1:
                indices[i] += 1
                break
            else:
                if i == len(indices) - 1:
                    indices = [0] * len(indices)
                    indices.append(0)
                    break
