import factory
import pytest

from peerinst.models import (
    Answer,
    AnswerChoice,
    Institution,
    Question,
    StudentGroupAssignment,
)
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.question.factories import CategoryFactory


class RealisticQuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    title = factory.Faker("sentence", nb_words=4)
    text = factory.Faker("paragraph")

    @factory.post_generation
    def category(self, *args, **kwargs):
        self.category.add(CategoryFactory())


class RealisticAnswerChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnswerChoice

    text = factory.Faker("paragraph")


@pytest.fixture
def realistic_questions():
    questions = [RealisticQuestionFactory() for _ in range(20)]
    # Add answer choices
    for q in questions:
        [
            RealisticAnswerChoiceFactory(question=q, correct=j == 2)
            for j in range(4)
        ]

    # One question with no answer choices
    questions.append(RealisticQuestionFactory())

    return questions


class InstitutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Institution

    name = factory.Faker("company")


@pytest.fixture
def institution():
    return InstitutionFactory()


@pytest.fixture
def undistributed_assignment(assignment, group):
    return StudentGroupAssignment.objects.create(
        assignment=assignment, group=group
    )


@pytest.fixture
def realistic_assignment(assignment, realistic_questions):
    qs = realistic_questions[:2]
    assignment.questions.set(qs)
    for q in qs:
        for i, _choice in enumerate(q.answerchoice_set.all()):
            Answer.objects.create(
                question=q,
                first_answer_choice=i + 1,
                rationale="rationale",
                second_answer_choice=i + 1,
                user_token="student1",
            )
            Answer.objects.create(
                question=q,
                first_answer_choice=i + 1,
                rationale="rationale",
                second_answer_choice=i + 1,
                expert=True,
            )
    return assignment
