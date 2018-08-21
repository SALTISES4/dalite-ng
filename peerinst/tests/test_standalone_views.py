# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
from datetime import datetime

from django.contrib.auth.hashers import make_password
from django.core import mail
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase, TransactionTestCase

from django.contrib.auth.models import User
from tos.models import Consent, Role, Tos
from ..models import StudentGroup

from .generators import *
from ..students import create_student_token, get_student_username_and_password
from ..utils import create_token


def ready_user(pk):
    user = User.objects.get(pk=pk)
    user.text_pwd = user.password
    user.password = make_password(user.text_pwd)
    user.save()
    return user


class StandaloneTest(TransactionTestCase):
    fixtures = ("test_users.yaml",)

    def setUp(self):
        self.validated_teacher = ready_user(1)

        # Skip TOS interactions
        role = Role.objects.get(role="teacher")
        tos = Tos(version=1, text="Test", current=True, role=role)
        tos.save()
        consent = Consent(
            user=self.validated_teacher, accepted=True, tos=Tos.objects.first()
        )
        consent.save()

        n_students = 15
        n_assignments = 1
        n_groups = 1
        n_questions = 10

        questions = add_questions(new_questions(n_questions))
        groups = add_groups(new_groups(n_groups))
        self.assignments = add_assignments(
            new_assignments(n_assignments, questions)
        )
        students = add_students(new_students(n_students))

        self.group = StudentGroup.objects.first()
        for student in students:
            student.groups.add(self.group)

        self.group.teacher.add(self.validated_teacher.teacher)
        self.validated_teacher.teacher.current_groups.add(self.group)

        self.assertEqual(self.group.student_set.count(), n_students)
        self.assertIn(
            self.group, self.validated_teacher.teacher.current_groups.all()
        )

    def test_standalone_workflow(self):
        # GET: Hash doesn't exist -> 404
        response = self.client.get(
            reverse(
                "signup-through-link",
                kwargs={
                    "group_hash": base64.urlsafe_b64encode(
                        str(1000000).encode()
                    ).decode()
                },
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("404.html")

        # GET: Hash exists -> 200, sign_up_student.html
        response = self.client.get(
            reverse(
                "signup-through-link", kwargs={"group_hash": self.group.hash}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("registration/sign_up_student.html")

        # POST: Email does not exist -> Create student, send email, sign_up_student_done.html
        response = self.client.post(
            reverse(
                "signup-through-link", kwargs={"group_hash": self.group.hash}
            ),
            {"email": "test@test.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("registration/sign_up_student_done.html")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Confirm myDALITE account")
        student = Student.objects.get(student__email="test@test.com")
        self.assertFalse(student.student.is_active)

        # Confirm registration
        username, password = get_student_username_and_password("test@test.com")
        token = create_student_token(username, "test@test.com")
        hash_ = self.group.hash
        response = self.client.get(
            reverse(
                "confirm-signup-through-link",
                kwargs={"group_hash": hash_, "token": token},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            "registration/sign_up_student_confirmation.html"
        )
        student = Student.objects.get(student__email="test@test.com")
        self.assertTrue(student.student.is_active)
        self.assertIn(StudentGroup.get(self.group.hash), student.groups.all())

        # Confirm registration, bad hash
        username, password = get_student_username_and_password("test@test.com")
        token = create_student_token(username, "test@test.com")
        hash_ = base64.urlsafe_b64encode(str(1000000).encode()).decode()
        response = self.client.get(
            reverse(
                "confirm-signup-through-link",
                kwargs={"group_hash": hash_, "token": token},
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("404.html")

        # Confirm registration, bad token (invalid)
        username, password = get_student_username_and_password("test@test.com")
        token = create_token(payload={"name": "test", "mail": "not_email"})
        hash_ = self.group.hash
        response = self.client.get(
            reverse(
                "confirm-signup-through-link",
                kwargs={"group_hash": hash_, "token": token},
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed("403.html")

        # Empty the test outbox
        mail.outbox = []

        # Create group assignment as teacher
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        response = self.client.post(
            reverse(
                "student-group-assignment-create",
                kwargs={"assignment_id": self.assignments[0].identifier},
            ),
            {
                "group": self.group.id,
                "due_date": datetime.now(),
                "show_correct_answers": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(StudentGroupAssignment.objects.count(), 1)
        self.assertEqual(len(mail.outbox), self.group.student_set.count())
        self.assertIn("New assignment", mail.outbox[0].subject)

        # Access as newly created student, expired
        assignment = StudentGroupAssignment.objects.first()
        response = self.client.get(
            reverse(
                "live",
                kwargs={
                    "token": create_student_token(username, "test@test.com"),
                    "assignment_hash": assignment.hash,
                },
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("peerinst/question_start.html")
