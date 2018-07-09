from __future__ import unicode_literals
import random
import string
from datetime import datetime

import pytz
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from tos.models import Consent, Tos, _compute_hash


class TestTosModel(TestCase):
    def test_new_tos(self):
        n = 5
        data = _new_tos(n, all_roles_present=True, random_current=True)
        first_for_role = {role[:2]: True for role in Tos.ROLES}

        for d in data:
            time = datetime.now(pytz.utc)
            tos = Tos.objects.create(**d)
            self.assertIsInstance(tos, Tos)
            self.assertEqual(tos.role, d["role"])
            self.assertEqual(tos.version, d["version"])
            self.assertEqual(tos.text, d["text"])
            if first_for_role[d["role"]]:
                self.assertEqual(tos.current, True)
                first_for_role[d["role"]] = False
            else:
                self.assertEqual(tos.current, d["current"])
            self.assertEqual(tos.hash, _compute_hash(d["text"]))
            self.assertGreater(tos.created, time)
            self.assertLess(tos.created, datetime.now(pytz.utc))

    def test_new_tos_version_exists(self):
        data = _new_tos(2, role=Tos.ROLES[0]) + _new_tos(1, role=Tos.ROLES[1])
        data[1]["version"] = data[0]["version"]
        data[2]["version"] = data[0]["version"]

        Tos.objects.create(**data[0])
        Tos.objects.create(**data[2])
        self.assertRaises(IntegrityError, Tos.objects.create, **data[1])

    def test_new_tos_hash_exists(self):
        data = _new_tos(2, role=Tos.ROLES[0]) + _new_tos(1, role=Tos.ROLES[1])
        data[1]["text"] = data[0]["text"]
        data[2]["text"] = data[0]["text"]

        Tos.objects.create(**data[0])
        Tos.objects.create(**data[2])
        self.assertRaises(IntegrityError, Tos.objects.create, **data[1])

    def test_get_tos(self):
        n_per_role = 5
        n = n_per_role * len(Tos.ROLES)
        tos_ = _add_tos(_new_tos(n, all_roles_present=True))
        tests = [
            {"role": role[:2], "version": version}
            for role in Tos.ROLES
            for version in [None] + list(range(n_per_role))
        ]

        for test in tests:
            tos, err = Tos.get(**test)
            self.assertIsInstance(tos, Tos)
            self.assertIs(err, None)
            if test["version"] is None:
                correct = [
                    t for t in tos_ if t.role == test["role"] and t.current
                ][0]
            else:
                correct = [
                    t
                    for t in tos_
                    if t.role == test["role"] and t.version == test["version"]
                ][0]
            self.assertEqual(tos.version, correct.version)
            self.assertEqual(tos.role, correct.role)
            self.assertEqual(tos.version, correct.version)
            self.assertEqual(tos.hash, correct.hash)
            self.assertEqual(tos.text, correct.text)
            self.assertEqual(tos.created, correct.created)

    def test_get_tos_no_version(self):
        tos_ = _add_tos(_new_tos(1, role=Tos.ROLES[0]))
        tests = [{"role": Tos.ROLES[1], "version": None}]

        for test in tests:
            tos, err = Tos.get(**test)
            self.assertIs(tos, None)
            self.assertEqual(
                err,
                'No terms of service exist yet for role "{}".'.format(
                    test["role"]
                ),
            )

    def test_get_tos_version_doesnt_exist(self):
        tos_ = _add_tos(_new_tos(1, role=Tos.ROLES[0]))
        tests = [{"role": Tos.ROLES[0], "version": len(tos_)}]

        for test in tests:
            tos, err = Tos.get(**test)
            self.assertIs(tos, None)
            self.assertEqual(
                err,
                "There is no terms of service with version "
                '{} for role "{}"'.format(test["version"], test["role"]),
            )


class TestConsent(TestCase):
    def test_new_consent(self):
        n_users = 10
        n_tos = 5
        n = 30
        users = _add_users(_new_user(n_users))
        tos = _add_tos(_new_tos(n_tos))
        data = _new_consent(n, users, tos)

        for d in data:
            time = datetime.now(pytz.utc)
            consent = Consent.objects.create(**d)
            self.assertIsInstance(consent, Consent)
            self.assertEqual(consent.user.username, d["user"].username)
            self.assertEqual(consent.tos.role, d["tos"].role)
            self.assertEqual(consent.tos.version, d["tos"].version)
            self.assertEqual(consent.accepted, d["accepted"])
            self.assertGreater(consent.datetime, time)
            self.assertLess(consent.datetime, datetime.now(pytz.utc))

    def test_get_consent(self):
        n_users = 10
        n_per_role = 2
        n_tos = n_per_role * len(Tos.ROLES)
        n_per_combination = 2
        n = n_per_combination * n_users * n_tos
        users = _add_users(_new_user(n_users))
        tos_ = _add_tos(_new_tos(n_tos, all_roles_present=True))
        consents = _add_consents(
            _new_consent(n, users, tos_, all_combinations_present=True)
        )

        tests = [
            {"username": user.username, "role": role, "version": version}
            for user in users
            for role in Tos.ROLES
            for version in [None] + list(range(n_per_role))
        ]

        for i, test in enumerate(tests):
            print("Failed at test: {}".format(i))
            consent = Consent.get(**test)
            self.assertIsInstance(consent, bool)
            if test["version"] is None:
                corrects = [
                    c
                    for c in Consent.objects.filter(
                        user__username=test["username"],
                        tos__role=test["role"][:2],
                        tos__current=True,
                    ).order_by("-datetime")
                ]
            else:
                corrects = [
                    c
                    for c in Consent.objects.filter(
                        user__username=test["username"],
                        tos__role=test["role"][:2],
                        tos__version=test["version"],
                    ).order_by("-datetime")
                ]
            for correct in corrects[1:]:
                self.assertGreater(corrects[0].datetime, correct.datetime)
            self.assertEqual(consent, corrects[0].accepted)

    def test_get_consent_doesnt_exist(self):
        n_users = 3
        n_per_role = 2
        n_tos = n_per_role * len(Tos.ROLES)
        n_per_combination = 2
        n = n_per_combination * n_users * n_tos
        users = _add_users(_new_user(n_users))
        tos_ = _add_tos(_new_tos(n_tos, all_roles_present=True))
        consents = _add_consents(
            _new_consent(
                n, users[:-1], tos_[:-1], all_combinations_present=True
            )
        )
        tests = [
            {"username": users[-1].username, "role": role, "version": version}
            for role in Tos.ROLES
            for version in [None] + list(range(n_per_role))
        ] + [
            {
                "username": users[-1].username,
                "role": tos_[-1].role,
                "version": tos_[-1].version,
            }
            for user in users
        ]

        for test in tests:
            consent = Consent.get(**test)
            self.assertIs(consent, None)


def _new_tos(n, role=None, all_roles_present=False, random_current=True):
    if role is None and all_roles_present:
        if n < len(Tos.ROLES):
            raise RuntimeError(
                "There aren't enough tos for all possible roles"
            )
        n_per_role = n // len(Tos.ROLES)
        gens = [_new_tos_gen(role=role) for role in Tos.ROLES]
        tos = []
        for gen in gens:
            tos += [next(gen) for _ in range(n_per_role)]
        if len(tos) != n:
            tos += [next(random.choice(gens)) for _ in range(n - len(tos))]
    else:
        gen = _new_tos_gen(role=role)
        tos = [next(gen) for _ in range(n)]
    if random_current:
        for role in {t["role"] for t in tos}:
            idx = [i for i, t in enumerate(tos) if t["role"] == role]
            tos[random.choice(idx)]["current"] = True
    return tos


def _new_tos_gen(role=None):
    letters = string.ascii_letters
    versions = {role: 0 for role in Tos.ROLES}
    random_char = {role: letters[versions[role]] for role in Tos.ROLES}
    while True:
        role_ = role or random.choice(Tos.ROLES)
        version = versions[role_]
        tos = {
            "role": role_[:2],
            "version": version,
            "text": "".join(
                letters[random.randrange(0, len(letters))]
                for _ in range(random.randint(1, 100))
            )
            + random_char[role_],
            "current": False,
        }
        yield tos
        versions[role_] += 1
        if versions < len(letters):
            random_char[role_] = letters[versions[role_]]
        else:
            random_char[role_] = (
                letters[versions[role_] % len(letters)]
                + letters[versions[role_] // len(letters)]
            )


def _add_tos(tos_):
    tos = [Tos.objects.create(**t) for t in tos_]
    current_idx = [
        max(i for i, t in enumerate(tos) if t.role == role and t.current)
        for role in {t.role for t in tos}
    ]
    for i, t in enumerate(tos):
        if i not in current_idx:
            t.current = False
    return tos


def _new_user(n):
    gen = _new_user_gen()
    user = [next(gen) for _ in range(n)]
    return user


def _new_user_gen():
    letters = string.ascii_letters
    chars = string.ascii_letters + string.digits + "_-."
    while True:
        user = {
            "username": "".join(
                letters[random.randrange(0, len(letters))]
                for _ in range(random.randint(1, 12))
            ),
            "email": "".join(
                chars[random.randrange(0, len(chars))]
                for _ in range(random.randrange(1, 32))
            )
            + "@"
            + "".join(
                letters[random.randrange(0, len(letters))]
                for _ in range(1, 10)
            )
            + "."
            + "".join(
                letters[random.randrange(0, len(letters))] for _ in range(2, 3)
            ),
            "password": "test",
        }
        yield user


def _add_users(users):
    return [User.objects.create_user(**u) for u in users]


def _new_consent(n, users, tos, all_combinations_present=False):
    if all_combinations_present:
        if n < len(users) * len(tos):
            raise RuntimeError(
                "There aren't enough consents for all possible users and tos"
            )
        n_per_combination = n // (len(users) * len(tos))
        gens = [_new_consent_gen([u], [t]) for u in users for t in tos]
        consents = []
        for gen in gens:
            consents += [next(gen) for _ in range(n_per_combination)]
        if len(consents) != n:
            consents += [
                next(random.choice(gens)) for _ in range(n - len(consents))
            ]
    else:
        gen = _new_consent_gen(users, tos)
        consents = [next(gen) for _ in range(n)]
    return consents


def _new_consent_gen(users, tos):
    while True:
        user = random.choice(users)
        tos_ = random.choice(tos)
        yield {"user": user, "tos": tos_, "accepted": random.random() > 0.5}


def _add_consents(consents):
    return [Consent.objects.create(**c) for c in consents]
