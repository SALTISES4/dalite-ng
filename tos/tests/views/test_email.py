import random

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from ..generators import (
    add_email_types,
    add_roles,
    add_users,
    new_email_consents,
    new_email_types,
    new_roles,
    new_users,
)
from .utils import login_user


class TestEmailConsentModifyView(TestCase):
    def setUp(self):
        self.client = Client()
        n_users = 1
        n_roles = 1
        n_email_types = 1
        n_consents = 1
        self.users = add_users(new_users(n_users))
        self.roles = add_roles(new_roles(n_roles))
        self.email_types = add_email_types(
            new_email_types(n_email_types, self.roles)
        )
        self.consents = new_email_consents(
            n_consents, self.users, self.email_types
        )
        for user in self.users:
            login_user(self.client, user)

    def test_consent_modify(self):
        tests = [{"role": role.role} for role in self.roles]

        for test in tests:
            resp = self.client.get(reverse("tos:email_modify", kwargs=test))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, "tos/email_modify.html")

    def test_consent_modify_wrong_method(self):
        tests = [{"role": role.role} for role in self.roles]

        for test in tests:
            resp = self.client.post(reverse("tos:email_modify", kwargs=test))
            self.assertEqual(resp.status_code, 405)

    def test_consent_modify_role_doesnt_exist(self):
        tests = [{"role": role.role + "fsaj"} for role in self.roles]

        for test in tests:
            resp = self.client.get(reverse("tos:email_modify", kwargs=test))
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "The role {} doesn't seem to exist.".format(test["role"]),
                resp.content.decode(),
            )


class TestEmailConsentUpdateView(TestCase):
    def setUp(self):
        self.client = Client()
        n_users = 1
        n_roles = 1
        n_email_types = 1
        n_consents = 1
        self.users = add_users(new_users(n_users))
        self.roles = add_roles(new_roles(n_roles))
        self.email_types = add_email_types(
            new_email_types(n_email_types, self.roles)
        )
        self.consents = new_email_consents(
            n_consents, self.users, self.email_types
        )
        for user in self.users:
            login_user(self.client, user)

    def test_consent_update(self):
        data = [
            {
                "email_type": email_type.type,
                "accepted": random.random() > 0.5,
                "role": role,
            }
            for role in self.roles
            for email_type in self.email_types
            if email_type.role == role
        ]
        tests = [
            (
                {"role": d["role"].role},
                {"{}-consent".format(d["email_type"]): True},
            )
            for d in data
            if d["accepted"]
        ]

        for test in tests:
            resp = self.client.post(
                reverse("tos:email_update", kwargs=test[0]), test[1]
            )
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, "/welcome/", target_status_code=302)

    def test_consent_update_wrong_method(self):
        tests = [{"role": role.role} for role in self.roles]

        for test in tests:
            resp = self.client.get(reverse("tos:email_update", kwargs=test))
            self.assertEqual(resp.status_code, 405)

    def test_consent_update_role_doesnt_exist(self):
        tests = [{"role": role.role + "fsaj"} for role in self.roles]

        for test in tests:
            resp = self.client.post(reverse("tos:email_update", kwargs=test))
            self.assertEqual(resp.status_code, 400)
            self.assertIn(
                "The role {} doesn't seem to exist.".format(test["role"]),
                resp.content.decode(),
            )
