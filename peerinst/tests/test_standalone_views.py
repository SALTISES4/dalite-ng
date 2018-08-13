
from datetime import datetime

from django.contrib.auth.hashers import make_password
from django.core import mail
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase, TransactionTestCase

from django.contrib.auth.models import User
from tos.models import Consent, Role, Tos

from .generators import *

def ready_user(pk):
    user = User.objects.get(pk=pk)
    user.text_pwd = user.password
    user.password = make_password(user.text_pwd)
    user.save()
    return user

class StandaloneTest(TransactionTestCase):
    fixture = ['test_users.yaml']

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
        assignments = add_assignments(
            new_assignments(n_assignments, questions)
        )
        students = add_students(new_students(n_students))

        self.group = StudentGroups.objects.first()
        for student in students:
            student.groups.add(group)

        self.assertEqual(group.student_set.count(), n_students)


    def test_create_group_assignment(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        response = self.client.post(reverse('create-group-assignment'), {
            'assignment_id' : 'Assignment2',
            'group_id' : self.group,
            'due_date' : datetime.now},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )

        self.assertTrue(StudentGroupAssignment.objects.count(), 1)
        self.assertEqual(len(mail.outbox), self.groups.student_set.count())
        self.assertEqual(
            mail.outbox[0].subject, "A new assignment is available"
        )

    def test_access_to_share_group(self):
        pass
