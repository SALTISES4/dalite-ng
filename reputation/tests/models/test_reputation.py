import pytest

from peerinst.models import Assignment, Question, Teacher
from peerinst.tests.fixtures import *  # noqa
from reputation.models import Reputation, ReputationType
from reputation.tests.fixtures import *  # noqa


def test_str(question_reputation, assignment_reputation, teacher_reputation):
    assert str(question_reputation) == "{} for question: {}".format(
        question_reputation.pk, str(question_reputation.reputation_model)
    )
    assert str(assignment_reputation) == "{} for assignment: {}".format(
        assignment_reputation.pk, str(assignment_reputation.reputation_model)
    )
    assert str(teacher_reputation) == "{} for teacher: {}".format(
        teacher_reputation.pk, str(teacher_reputation.reputation_model)
    )


def test_str__unkown_reputation():
    reputation_type = ReputationType.objects.get(type="teacher")
    reputation = Reputation.objects.create(reputation_type=reputation_type)
    assert str(reputation).endswith("Unknown")


def test_reputation_model(
    question_reputation, assignment_reputation, teacher_reputation
):
    assert isinstance(question_reputation.reputation_model, Question)
    assert isinstance(assignment_reputation.reputation_model, Assignment)
    assert isinstance(teacher_reputation.reputation_model, Teacher)


def test_reputation_model__no_onetoone(question_reputation):
    model = question_reputation.question
    model.reputation = None
    model.save()
    with pytest.raises(ValueError):
        question_reputation.reputation_model


def test_create__str_passed():
    for cls in ("Question", "Assignment", "Teacher"):
        reputation = Reputation.create(cls)
        assert isinstance(reputation, Reputation)
        assert reputation.reputation_type.type == cls.lower()


def test_create__object_passed(question, assignment, teacher):
    for cls in (question, assignment, teacher):
        reputation = Reputation.create(cls)
        assert isinstance(reputation, Reputation)
        assert (
            reputation.reputation_type.type == cls.__class__.__name__.lower()
        )


def test_create__wrong_type():
    with pytest.raises(ReputationType.DoesNotExist):
        reputation = Reputation.create("StudentAssignment")
