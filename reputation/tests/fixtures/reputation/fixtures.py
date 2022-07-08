import pytest

from peerinst.tests.fixtures import *  # noqa
from reputation.models import Reputation, ReputationType


@pytest.fixture
def question_reputation(question):
    reputation_type = ReputationType.objects.get(type="question")
    reputation = Reputation.objects.create(reputation_type=reputation_type)
    question.reputation = reputation
    question.save()
    return reputation


@pytest.fixture
def assignment_reputation(assignment):
    reputation_type = ReputationType.objects.get(type="assignment")
    reputation = Reputation.objects.create(reputation_type=reputation_type)
    assignment.reputation = reputation
    assignment.save()
    return reputation


@pytest.fixture
def teacher_reputation(teacher):
    reputation_type = ReputationType.objects.get(type="teacher")
    reputation = Reputation.objects.create(reputation_type=reputation_type)
    teacher.reputation = reputation
    teacher.save()
    return reputation


@pytest.fixture
def student_reputation(student):
    reputation_type = ReputationType.objects.get(type="student")
    reputation = Reputation.objects.create(reputation_type=reputation_type)
    student.reputation = reputation
    student.save()
    return reputation
