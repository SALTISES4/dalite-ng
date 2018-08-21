import random
from datetime import datetime, timedelta
from operator import itemgetter

import pytz
from django.test import TestCase

from peerinst.models import StudentGroupAssignment
from peerinst.tests.generators import (
    add_answer_choices,
    add_answers,
    add_assignments,
    add_groups,
    add_questions,
    add_student_assignments,
    add_student_group_assignments,
    add_students,
    add_to_group,
    new_assignments,
    new_groups,
    new_questions,
    new_student_assignments,
    new_student_group_assignments,
    new_students,
)


class TestNewStudentGroupAssignment(TestCase):
    def setUp(self):
        questions = add_questions(new_questions(100))
        self.groups = add_groups(new_groups(2))
        self.assignments = add_assignments(new_assignments(20, questions))

    def test_working(self):
        n = 10
        data = new_student_group_assignments(n, self.groups, self.assignments)

        for d in data:
            group = StudentGroupAssignment.objects.create(**d)
            n = len(group.assignment.questions.all())
            self.assertIsInstance(group, StudentGroupAssignment)
            self.assertEqual(group.group, d["group"])
            self.assertEqual(group.assignment, d["assignment"])
            self.assertEqual(group.order, ",".join(map(str, range(n))))


class TestIsExpired(TestCase):
    def setUp(self):
        questions = add_questions(new_questions(100))
        self.groups = add_groups(new_groups(2))
        self.assignments = add_assignments(new_assignments(20, questions))

    def test_expired(self):
        assignment = add_student_group_assignments(
            new_student_group_assignments(
                1,
                self.groups,
                self.assignments,
                due_date=datetime.now(pytz.utc),
            )
        )[0]
        self.assertTrue(assignment.is_expired())

    def test_not_expired(self):
        assignment = add_student_group_assignments(
            new_student_group_assignments(
                1,
                self.groups,
                self.assignments,
                due_date=datetime.now(pytz.utc) + timedelta(days=1),
            )
        )[0]
        self.assertTrue(not assignment.is_expired())


class TestHashing(TestCase):
    def setUp(self):
        questions = add_questions(new_questions(100))
        self.groups = add_groups(new_groups(2))
        self.assignments = add_assignments(new_assignments(20, questions))

    def test_working(self):
        n = 10
        assignments = add_student_group_assignments(
            new_student_group_assignments(n, self.groups, self.assignments)
        )

        for assignment in assignments:
            self.assertEqual(
                assignment, StudentGroupAssignment.get(assignment.hash)
            )


class TestModifyOrder(TestCase):
    def setUp(self):
        questions = add_questions(new_questions(100))
        self.groups = add_groups(new_groups(2))
        self.assignments = add_assignments(new_assignments(20, questions))

    def test_working(self):
        n = 2
        assignments = add_student_group_assignments(
            new_student_group_assignments(n, self.groups, self.assignments)
        )

        for assignment in assignments:
            k = len(assignment.assignment.questions.all())
            new_order = ",".join(map(str, random.sample(range(k), k=k)))
            err = assignment.modify_order(new_order)
            self.assertIs(err, None)
            self.assertEqual(new_order, assignment.order)

    def test_wrong_type(self):
        n = 1
        assignment = add_student_group_assignments(
            new_student_group_assignments(n, self.groups, self.assignments)
        )[0]

        new_order = [1, 2, 3]
        self.assertRaises(AssertionError, assignment.modify_order, new_order)

        new_order = "abc"
        err = assignment.modify_order(new_order)
        self.assertEqual(
            err, "Given `order` isn't a comma separated list of integers."
        )

        new_order = "a,b,c"
        err = assignment.modify_order(new_order)
        self.assertEqual(
            err, "Given `order` isn't a comma separated list of integers."
        )

    def test_wrong_values(self):
        n = 1
        assignment = add_student_group_assignments(
            new_student_group_assignments(n, self.groups, self.assignments)
        )[0]

        n = len(assignment.assignment.questions.all())

        data = ("-1,2,3", "1,2,{}".format(n), "1,1,2")

        errors = (
            "Given `order` has negative values.",
            (
                "Given `order` has at least one value bigger than the number "
                "of questions."
            ),
            "There are duplicate values in `order`.",
        )

        for d, e in zip(data, errors):
            err = assignment.modify_order(d)
            self.assertEqual(err, e)


class TestGetStudentProgress(TestCase):
    def setUp(self):
        n_questions = 3
        self.students = add_students(new_students(20))
        groups = add_groups(new_groups(1))
        add_to_group(self.students, groups)
        self.questions = add_questions(new_questions(n_questions))
        add_answer_choices(2, self.questions)
        assignments = add_assignments(
            new_assignments(1, self.questions, min_questions=n_questions)
        )
        self.assignment = add_student_group_assignments(
            new_student_group_assignments(1, groups, assignments)
        )[0]
        student_assignments = add_student_assignments(
            new_student_assignments(
                len(self.students), [self.assignment], self.students
            )
        )

    def test_no_questions_done(self):
        progress = self.assignment.get_student_progress()

        self.assertEqual(
            0,
            len(
                set(map(itemgetter("question_title"), progress))
                - set((q.title for q in self.questions))
            ),
        )
        for question in progress:
            self.assertEqual(len(self.students), len(question["students"]))
            self.assertEqual(0, question["first"])
            self.assertEqual(0, question["first_correct"])
            self.assertEqual(0, question["second"])
            self.assertEqual(0, question["second_correct"])

    def test_some_first_answers_done(self):
        times_answered = {
            q.pk: random.randrange(1, len(self.students))
            for q in self.questions
        }
        answers = add_answers(
            [
                {
                    "question": question,
                    "assignment": self.assignment.assignment,
                    "user_token": student.student.username,
                    "first_answer_choice": 1,
                    "rationale": "test",
                }
                for question in self.questions
                for student in self.students[: times_answered[question.pk]]
            ]
        )

        progress = self.assignment.get_student_progress()

        self.assertEqual(
            0,
            len(
                set(map(itemgetter("question_title"), progress))
                - set((q.title for q in self.questions))
            ),
        )
        for question in progress:
            question_ = next(
                q
                for q in self.questions
                if q.title == question["question_title"]
            )
            self.assertEqual(len(self.students), len(question["students"]))
            self.assertEqual(times_answered[question_.pk], question["first"])
            self.assertEqual(
                times_answered[question_.pk], question["first_correct"]
            )
            self.assertEqual(0, question["second"])
            self.assertEqual(0, question["second_correct"])

    def test_all_first_answers_done(self):
        answers = add_answers(
            [
                {
                    "question": question,
                    "assignment": self.assignment.assignment,
                    "user_token": student.student.username,
                    "first_answer_choice": 1,
                    "rationale": "test",
                }
                for question in self.questions
                for student in self.students
            ]
        )

        progress = self.assignment.get_student_progress()

        self.assertEqual(
            0,
            len(
                set(map(itemgetter("question_title"), progress))
                - set((q.title for q in self.questions))
            ),
        )
        for question in progress:
            self.assertEqual(len(self.students), len(question["students"]))
            self.assertEqual(len(self.students), question["first"])
            self.assertEqual(len(self.students), question["first_correct"])
            self.assertEqual(0, question["second"])
            self.assertEqual(0, question["second_correct"])

    def test_some_second_answers_done(self):
        times_first_answered = {
            q.pk: random.randrange(2, len(self.students))
            for q in self.questions
        }
        times_second_answered = {
            q.pk: random.randrange(1, times_first_answered[q.pk])
            for q in self.questions
        }
        answers = add_answers(
            [
                {
                    "question": question,
                    "assignment": self.assignment.assignment,
                    "user_token": student.student.username,
                    "first_answer_choice": 1,
                    "rationale": "test",
                }
                for question in self.questions
                for student in self.students[
                    times_second_answered[question.pk] : times_first_answered[
                        question.pk
                    ]
                ]
            ]
        )
        answers += add_answers(
            [
                {
                    "question": question,
                    "assignment": self.assignment.assignment,
                    "user_token": student.student.username,
                    "first_answer_choice": 1,
                    "rationale": "test",
                    "second_answer_choice": 1,
                    "chosen_rationale": random.choice(
                        [a for a in answers if a.question == question]
                    ),
                }
                for question in self.questions
                for student in self.students[
                    : times_second_answered[question.pk]
                ]
            ]
        )

        progress = self.assignment.get_student_progress()

        self.assertEqual(
            0,
            len(
                set(map(itemgetter("question_title"), progress))
                - set((q.title for q in self.questions))
            ),
        )
        for question in progress:
            question_ = next(
                q
                for q in self.questions
                if q.title == question["question_title"]
            )
            self.assertEqual(len(self.students), len(question["students"]))
            self.assertEqual(
                times_first_answered[question_.pk], question["first"]
            )

            self.assertEqual(
                times_first_answered[question_.pk], question["first_correct"]
            )
            self.assertEqual(
                times_second_answered[question_.pk], question["second"]
            )
            self.assertEqual(
                times_second_answered[question_.pk], question["second_correct"]
            )

    def test_all_second_answers_done(self):

        answers = add_answers(
            [
                {
                    "question": question,
                    "assignment": self.assignment.assignment,
                    "user_token": student.student.username,
                    "first_answer_choice": 1,
                    "rationale": "test",
                    "second_answer_choice": 1,
                    "chosen_rationale": None,
                }
                for question in self.questions
                for student in self.students
            ]
        )

        progress = self.assignment.get_student_progress()

        self.assertEqual(
            0,
            len(
                set(map(itemgetter("question_title"), progress))
                - set((q.title for q in self.questions))
            ),
        )
        for question in progress:
            self.assertEqual(len(self.students), len(question["students"]))
            self.assertEqual(len(self.students), question["first"])
            self.assertEqual(len(self.students), question["first_correct"])
            self.assertEqual(len(self.students), question["second"])
            self.assertEqual(len(self.students), question["second_correct"])


class TestQuestions(TestCase):
    def setUp(self):
        questions = add_questions(new_questions(10))
        self.groups = add_groups(new_groups(2))
        self.assignments = add_assignments(new_assignments(20, questions))

    def test_working(self):
        n = 2
        assignments = add_student_group_assignments(
            new_student_group_assignments(n, self.groups, self.assignments)
        )

        for assignment in assignments:
            k = len(assignment.questions)
            new_order = ",".join(map(str, random.sample(range(k), k=k)))
            err = assignment.modify_order(new_order)
            self.assertIs(err, None)
            for i, j in enumerate(map(int, new_order.split(","))):
                self.assertEqual(
                    assignment.questions[i],
                    assignment.assignment.questions.all()[j],
                )

            self.assertEqual(new_order, assignment.order)


class TestGetQuestion(TestCase):
    def setUp(self):
        questions = add_questions(new_questions(10))
        groups = add_groups(new_groups(1))
        assignments = add_assignments(new_assignments(1, questions))
        self.assignment = add_student_group_assignments(
            new_student_group_assignments(1, groups, assignments)
        )[0]

    def test_get_question_by_idx(self):
        questions = self.assignment.questions

        for idx in range(len(questions)):
            question_ = self.assignment.get_question(idx=idx)
            self.assertEqual(questions[idx], question_)

    def test_get_question_current_question_regular(self):
        questions = self.assignment.questions

        for i, question in enumerate(questions):
            if i != 0 and i != len(questions) - 1:
                question_ = self.assignment.get_question(
                    current_question=question, after=True
                )
                self.assertEqual(question_, questions[i + 1])
                question_ = self.assignment.get_question(
                    current_question=question, after=False
                )
                self.assertEqual(question_, questions[i - 1])

    def test_get_question_current_question_edges(self):
        questions = self.assignment.questions

        question_ = self.assignment.get_question(
            current_question=questions[0], after=False
        )
        self.assertIs(question_, None)
        question_ = self.assignment.get_question(
            current_question=questions[-1], after=True
        )
        self.assertIs(question_, None)

    def test_get_question_assert_raised(self):
        pass
        # To be revised with assertions in method
        #self.assertRaises(
        #    AssertionError,
        #    self.assignment.get_question,
        #    (0, self.assignment.questions[0]),
        #)
