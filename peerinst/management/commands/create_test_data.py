from datetime import timedelta
from math import ceil

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from peerinst.models import (
    Answer,
    AnswerChoice,
    Assignment,
    Question,
    Student,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)
from peerinst.students import get_student_username_and_password


class Command(BaseCommand):
    help = "Create test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--n-students",
            type=int,
            default=24,
            help="Number of students to create",
        )
        parser.add_argument(
            "--n-groups",
            type=int,
            default=1,
            help="Number of groups to create",
        )
        parser.add_argument(
            "--n-questions",
            type=int,
            default=8,
            help="Number of questions to create",
        )
        parser.add_argument(
            "--n-assignments",
            type=int,
            default=1,
            help="Number of assignments to create",
        )

    def handle(self, *args, **kwargs):
        n_students = kwargs["n_students"]
        n_groups = kwargs["n_groups"]
        n_questions = kwargs["n_questions"]
        n_assignments = kwargs["n_assignments"]

        teacher = get_teacher()
        students = get_students(n_students)
        groups = get_groups(teacher, students, n_groups)
        questions = get_questions(teacher, n_questions)
        assignments = get_assignments(
            teacher, groups, questions, n_assignments
        )
        answer_assignments(assignments, students)


def get_teacher():
    user, _ = User.objects.get_or_create(username="_test")
    user.set_password("test")
    user.save()
    return Teacher.objects.get_or_create(user=user)[0]


def get_students(n_students):
    emails = [f"test-{i + 1}@test.com" for i in range(n_students)]
    usernames_passwords = [
        get_student_username_and_password(email) for email in emails
    ]

    users = [
        User.objects.get_or_create(username=username[0], email=email)[0]
        for username, email in zip(usernames_passwords, emails)
    ]
    for user, password in zip(users, usernames_passwords):
        user.set_password(password[1])
        user.save()

    return [Student.objects.get_or_create(student=user)[0] for user in users]


def get_groups(teacher, students, n_groups):
    groups = [
        StudentGroup.objects.get_or_create(
            name=f"_test-{i + 1}", title=f"Test {i + 1}"
        )[0]
        for i in range(n_groups)
    ]
    for group in groups:
        group.teacher.set([teacher])
        group.save()

    teacher.current_groups.set(groups)

    for student in students:
        for group in groups:
            student.join_group(group)

    return groups


def get_questions(teacher, n_questions):
    questions = [
        Question.objects.get_or_create(
            title=f"_Test {i + 1}",
            text=f"_Test {i + 1}",
            user=teacher.user,
        )[0]
        for i in range(n_questions)
    ]

    for question in questions:
        for choice in ("a", "b"):
            AnswerChoice.objects.get_or_create(
                question=question, text=choice, correct=choice == "a"
            )

    return questions


def get_assignments(teacher, groups, questions, n_assignments):
    assignments = [
        Assignment.objects.get_or_create(
            identifier=f"_test {i + 1}", title=f"Test {i + 1}"
        )[0]
        for i in range(n_assignments)
    ]
    for assignment in assignments:
        assignment.owner.set([teacher.user])
        assignment.questions.set(questions)

    teacher.assignments.set(assignments)
    teacher.save()

    group_assignments = [
        StudentGroupAssignment.objects.get_or_create(
            group=group, assignment=assignment
        )[0]
        for assignment in assignments
        for group in groups
    ]

    for assignment in group_assignments:
        assignment.due_date = timezone.now() + timedelta(days=7)
        assignment.save()
        assignment.distribute()

    return group_assignments


def answer_assignments(assignments, students):
    for assignment in assignments:
        for i, question in enumerate(assignment.assignment.questions.all()):
            q = assignment.assignment.questions.count()
            n = int(ceil(float(i + 1) * len(students) / q))
            for j, student in enumerate(students[: n + 1]):
                if (i + 1) % 8 == 2:
                    if j < float(n) / 2:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            user_token=student.student.username,
                        )
                elif (i + 1) % 8 == 3:
                    Answer.objects.get_or_create(
                        question=question,
                        assignment=assignment.assignment,
                        rationale="test",
                        first_answer_choice=1,
                        user_token=student.student.username,
                    )
                elif (i + 1) % 8 == 4:
                    if j < float(n) / 2:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            user_token=student.student.username,
                        )
                    else:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=2,
                            user_token=student.student.username,
                        )
                elif (i + 1) % 8 == 5:
                    if j < float(n) / 2:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            second_answer_choice=1,
                            user_token=student.student.username,
                        )
                    else:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            second_answer_choice=2,
                            user_token=student.student.username,
                        )
                elif (i + 1) % 8 == 6:
                    if j < float(n) / 3:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            second_answer_choice=1,
                            user_token=student.student.username,
                        )
                    elif j < 2.0 * float(n) / 3:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            second_answer_choice=2,
                            user_token=student.student.username,
                        )
                    else:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=2,
                            second_answer_choice=2,
                            user_token=student.student.username,
                        )
                elif (i + 1) % 8 == 7:
                    if j < float(n) / 3:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=1,
                            second_answer_choice=1,
                            user_token=student.student.username,
                        )
                    elif j < 2.0 * float(n) / 3:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=2,
                            second_answer_choice=2,
                            user_token=student.student.username,
                        )
                    else:
                        Answer.objects.get_or_create(
                            question=question,
                            assignment=assignment.assignment,
                            rationale="test",
                            first_answer_choice=2,
                            second_answer_choice=2,
                            user_token=student.student.username,
                        )
                else:
                    Answer.objects.get_or_create(
                        question=question,
                        assignment=assignment.assignment,
                        rationale="test",
                        first_answer_choice=1,
                        second_answer_choice=1,
                        user_token=student.student.username,
                    )
