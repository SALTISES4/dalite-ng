import json
import random

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from ..generators import (
    add_roles,
    add_tos,
    add_tos_consents,
    add_users,
    new_roles,
    new_tos,
    new_tos_consents,
    new_users,
)
from .utils import login_user


class TestTosConsentView(TestCase):
    def setUp(self):
        self.client = Client()
        n_users = 1
        n_roles = 1
        n_tos = 1
        n_consent = 1
        self.users = add_users(new_users(n_users))
        self.roles = add_roles(new_roles(n_roles))
        self.tos = add_tos(new_tos(n_tos, self.roles))
        self.consents = new_tos_consents(n_consent, self.users, self.tos)
        for user in self.users:
            login_user(self.client, user)

    def test_consent_exists_and_is_true(self):
        self.consents[0]["accepted"] = True
        add_tos_consents(self.consents)

        tests = [
            {"role": self.roles[0].role},
            {"role": self.roles[0].role, "version": int(self.tos[0].version)},
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_consent", kwargs=test))
            self.assertEqual(resp.status_code, 200)
            body = json.loads(resp.content.decode())
            self.assertEqual(body["consent"], True)

    def test_consent_exists_and_is_false(self):
        self.consents[0]["accepted"] = False
        add_tos_consents(self.consents)

        tests = [
            {"role": self.roles[0].role},
            {"role": self.roles[0].role, "version": int(self.tos[0].version)},
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_consent", kwargs=test))
            body = json.loads(resp.content.decode())
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(body["consent"], False)

    def test_consent_doesnt_exist_yet(self):
        tests = [
            {"role": self.roles[0].role},
            {"role": self.roles[0].role, "version": int(self.tos[0].version)},
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_consent", kwargs=test))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, "tos/tos_modify.html")

    def test_consent_version_doesnt_exist(self):
        tests = [
            {
                "role": self.roles[0].role,
                "version": int(self.tos[0].version) + 1,
            }
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_consent", kwargs=test))
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "There is no terms of service with version "
                "{} for role {}".format(test["version"], test["role"]),
                resp.content.decode(),
            )

    def test_consent_wrong_method(self):
        tests = [{"role": self.roles[0].role}]
        for test in tests:
            resp = self.client.post(reverse("tos:tos_consent", kwargs=test))
            self.assertEqual(resp.status_code, 405)

    def test_consent_invalid_role(self):
        tests = [{"role": self.roles[0].role + "fdsa"}]
        for test in tests:
            resp = self.client.get(reverse("tos:tos_consent", kwargs=test))
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "{} isn't a valid role.".format(test["role"]),
                resp.content.decode(),
            )


class TestTosConsentModifyView(TestCase):
    def setUp(self):
        self.client = Client()
        n_users = 1
        n_roles = 1
        n_tos = 1
        n_consent = 1
        self.users = add_users(new_users(n_users))
        self.roles = add_roles(new_roles(n_roles))
        self.tos = add_tos(new_tos(n_tos, self.roles))
        self.consents = new_tos_consents(n_consent, self.users, self.tos)
        for user in self.users:
            login_user(self.client, user)

    def test_consent_modify(self):
        tests = [
            {"role": self.roles[0].role},
            {"role": self.roles[0].role, "version": int(self.tos[0].version)},
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_modify", kwargs=test))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, "tos/tos_modify.html")

    def test_consent_modify_already_exists(self):
        tests = [
            {"role": self.roles[0].role},
            {"role": self.roles[0].role, "version": int(self.tos[0].version)},
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_modify", kwargs=test))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, "tos/tos_modify.html")

    def test_consent_modify_version_doesnt_exist(self):
        tests = [
            {
                "role": self.roles[0].role,
                "version": int(self.tos[0].version) + 1,
            }
        ]

        for test in tests:
            resp = self.client.get(reverse("tos:tos_modify", kwargs=test))
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "There is no terms of service with version "
                "{} for role {}".format(test["version"], test["role"]),
                resp.content.decode(),
            )

    def test_consent_modify_wrong_method(self):
        tests = [{"role": self.roles[0].role, "version": 0}]
        for test in tests:
            resp = self.client.post(reverse("tos:tos_modify", kwargs=test))
            self.assertEqual(resp.status_code, 405)

    def test_consent_modify_invalid_role(self):
        tests = [{"role": self.roles[0].role + "fdas", "version": 0}]
        for test in tests:
            resp = self.client.get(reverse("tos:tos_modify", kwargs=test))
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "{} isn't a valid role.".format(test["role"]),
                resp.content.decode(),
            )


class TestTosConsentUpdateView(TestCase):
    def setUp(self):
        self.client = Client()
        n_users = 1
        n_roles = 2
        n_tos = 1
        n_consent = 1
        self.users = add_users(new_users(n_users))
        self.roles = add_roles(new_roles(n_roles))
        self.tos = add_tos(new_tos(n_tos, [self.roles[0]])) + add_tos(
            new_tos(n_tos, [self.roles[1]])
        )
        self.consents = new_tos_consents(n_consent, self.users, self.tos)
        for user in self.users:
            login_user(self.client, user)

    def test_consent_update_accepted(self):
        tests = [
            (
                {
                    "role": self.roles[0].role,
                    "version": int(self.tos[0].version),
                },
                {"accepted": True},
            )
        ]

        for test in tests:
            resp = self.client.post(
                reverse("tos:tos_update", kwargs=test[0]), test[1]
            )
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, "/welcome/", target_status_code=302)

    def test_consent_update_refused(self):
        tests = [
            (
                {
                    "role": self.roles[0].role,
                    "version": int(self.tos[0].version),
                },
                {"accepted": False},
            )
        ]

        for test in tests:
            resp = self.client.post(
                reverse("tos:tos_update", kwargs=test[0]), test[1]
            )
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, "/welcome/", target_status_code=302)

    def test_consent_update_redirect(self):
        tests = [
            (
                {
                    "role": self.roles[0].role,
                    "version": int(self.tos[0].version),
                },
                {
                    "accepted": True,
                    "redirect_to": f"/tos/tos/{self.roles[1].role}/",
                },
            )
        ]

        for test in tests:
            resp = self.client.post(
                reverse("tos:tos_update", kwargs=test[0]), test[1]
            )
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(
                resp,
                f"/tos/tos/{self.roles[1].role}/",
                target_status_code=302,
            )

    def test_consent_update_version_doesnt_exist(self):
        tests = [
            (
                {
                    "role": self.roles[0].role,
                    "version": int(self.tos[0].version) + 1,
                },
                {"accepted": random.random() > 0.5},
            )
        ]

        for test in tests:
            resp = self.client.post(
                reverse("tos:tos_update", kwargs=test[0]), test[1]
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "There is no terms of service with version "
                "{} for role {}".format(test[0]["version"], test[0]["role"]),
                resp.content.decode(),
            )

    def test_consent_update_wrong_method(self):
        tests = [
            {"role": self.roles[0].role, "version": int(self.tos[0].version)}
        ]
        for test in tests:
            resp = self.client.get(reverse("tos:tos_update", kwargs=test))
            self.assertEqual(resp.status_code, 405)

    def test_consent_update_invalid_role(self):
        tests = [
            (
                {"role": self.roles[0].role + "fdsa", "version": 0},
                {"accepted": random.random() > 0.5},
            )
        ]
        for test in tests:
            resp = self.client.post(
                reverse("tos:tos_update", kwargs=test[0]), test[1]
            )
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "{} isn't a valid role.".format(test[0]["role"]),
                resp.content.decode(),
            )
