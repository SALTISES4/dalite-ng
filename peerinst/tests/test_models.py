from django.test import TestCase

from ..models import GradingScheme
from . import factories


class SelectedChoice:
    CORRECT = 1
    INCORRECT = 2


class AnswerModelTestCase(TestCase):
    def setUp(self):
        super().setUp()
        # Create question with two choices (correct/incorrect):
        self.question = factories.QuestionFactory(
            choices=2, choices__correct=[1]
        )
        # Create answers for question, considering all possible combinations of
        # correctness values:
        self.answers = []
        selected_choices = (
            (SelectedChoice.CORRECT, SelectedChoice.CORRECT),
            (SelectedChoice.CORRECT, SelectedChoice.INCORRECT),
            (SelectedChoice.INCORRECT, SelectedChoice.CORRECT),
            (SelectedChoice.INCORRECT, SelectedChoice.INCORRECT),
        )
        for first_answer_choice, second_answer_choice in selected_choices:
            answer = factories.AnswerFactory(
                question=self.question,
                first_answer_choice=first_answer_choice,
                second_answer_choice=second_answer_choice,
            )
            self.answers.append(answer)

    def _assert_grades(self, expected_grades):
        """
        For each answer in `self.answers`, check if `grade` produces
        correct value.
        """
        for index, answer in enumerate(self.answers):
            grade = answer.grade
            self.assertEqual(grade, expected_grades[index])

    def test_grade_standard(self):
        """
        Check if `grade` produces correct values when using 'Standard'
        grading scheme.

        | First choice | Second choice | Grade |
        |--------------+---------------+-------|
        | correct      | correct       | 1.0   |
        | correct      | incorrect     | 0.0   |
        | incorrect    | correct       | 1.0   |
        | incorrect    | incorrect     | 0.0   |
        """
        self._assert_grades(expected_grades=[1.0, 0.0, 1.0, 0.0])

    def test_grade_advanced(self):
        """
        Check if `grade` produces correct values when using 'Advanced'
        grading scheme.

        | First choice | Second choice | Grade |
        |--------------+---------------+-------|
        | correct      | correct       | 1.0   |
        | correct      | incorrect     | 0.5   |
        | incorrect    | correct       | 0.5   |
        | incorrect    | incorrect     | 0.0   |
        """
        self.question.grading_scheme = GradingScheme.ADVANCED
        self._assert_grades(expected_grades=[1.0, 0.5, 0.5, 0.0])
