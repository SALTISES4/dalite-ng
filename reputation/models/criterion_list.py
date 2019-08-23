# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import importlib

from ..logger import logger
from .criteria.errors import CriterionDoesNotExistError

criteria = {
    "common_rationale_choices": "CommonRationaleChoicesCriterion",
    "convincing_rationales": "ConvincingRationalesCriterion",
    "n_answers": "NAnswersCriterion",
    "n_questions": "NQuestionsCriterion",
    "question_liked_criterion": "QuestionLikedCriterion",
}


def get_criterion(criterion):
    """
    Returns the criterion class corresponding to the given `criterion` name.

    Parameters
    ----------
    criterion : str
        Name of the criterion

    Returns
    -------
    Criterion class
        Corresponding criterion class

    Raises
    ------
    CriterionDoesNotExistError
        If there is not criterion corresponding to the name `criterion`
    """
    try:
        return getattr(
            importlib.import_module(
                ".criteria", package=".".join(__name__.split(".")[:-1])
            ),
            criteria[criterion],
        )
    except (KeyError, AttributeError):
        msg = "There is not criterion with the name {}.".format(criterion)
        logger.error(msg)
        raise CriterionDoesNotExistError(msg)
