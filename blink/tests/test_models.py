from random import shuffle

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase

from blink.models import (
    BlinkAssignment,
    BlinkAssignmentQuestion,
    BlinkQuestion,
)
from peerinst.models import Question, Teacher


def ready_user(pk):
    user = User.objects.get(pk=pk)
    user.text_pwd = user.password
    user.password = make_password(user.text_pwd)
    user.save()
    return user


class BlinkAssignmentTestCase(TestCase):
    fixtures = ["test_users.yaml"]
    test_title = "testA1"
    test_key = "123"

    def setUp(self):
        self.validated_teacher = ready_user(1)
        self.teacher = Teacher.objects.get(user=self.validated_teacher)
        self.blinkassignment = BlinkAssignment.objects.create(
            title=self.test_title, teacher=self.teacher, key=self.test_key
        )
        qs = Question.objects.all()
        self.ranks = list(range(len(qs)))
        shuffle(self.ranks)

        for r, q in zip(self.ranks, qs):
            bq = BlinkQuestion(question=q, key=q.id)
            bq.save()

            assignment_ordering = BlinkAssignmentQuestion(
                blinkassignment=self.blinkassignment, blinkquestion=bq, rank=r
            )
            assignment_ordering.save()

        self.assertEqual(
            self.blinkassignment.blinkquestions.all().count(), len(self.ranks)
        )

    def test_move_down_rank(self):
        print("Move down")
        print((self.blinkassignment.blinkassignmentquestion_set.all()))
        this_q = self.blinkassignment.blinkassignmentquestion_set.get(rank=0)
        this_q_rank = this_q.rank
        print(this_q)
        print((this_q.rank))
        this_q.move_down_rank()
        this_q.save()
        print((self.blinkassignment.blinkassignmentquestion_set.all()))

        self.assertEqual(
            self.blinkassignment.blinkassignmentquestion_set.get(
                rank=this_q_rank + 1
            ),
            this_q,
        )

    def test_move_up_rank(self):
        print("Move up")
        print((self.blinkassignment.blinkassignmentquestion_set.all()))
        this_q = self.blinkassignment.blinkassignmentquestion_set.get(rank=2)
        this_q_rank = this_q.rank
        print(this_q)
        print((this_q.rank))
        this_q.move_up_rank()
        print((this_q.rank))
        this_q.save()
        print((self.blinkassignment.blinkassignmentquestion_set.all()))

        self.assertEqual(
            self.blinkassignment.blinkassignmentquestion_set.get(
                rank=this_q_rank - 1
            ),
            this_q,
        )
