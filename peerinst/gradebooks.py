# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from django.db.models.functions import Lower

from .models import (
    Answer,
    StudentGroup,
    StudentGroupAssignment,
    StudentGroupMembership,
)


class Echo:
    """
    https://docs.djangoproject.com/en/1.8/howto/outputting-csv/#streaming-large-csv-files
    An object that implements just the write method of a file-like interface
    """

    def write(self, value):
        """
        Write the value by returning it, instead of storing in buffer
        """
        return value


def compute_gradebook(group_pk, assignment_pk=None):
    """
    Computes the gradebook for the given group and assignment (if not None).

    Parameters
    ----------
    group_pk : int
        Primary key of the group for which to compute the gradebook
    assignment_pk : Optional[int] (default : None)
        Primary key of the assignment for which to compute the gradebook

    Returns
    -------
    Either
        If group gradebook wanted
            {
                group: str
                    Title of the group
                assignments: List[str]
                    Assignment identifier
                school_id_needed: bool
                    If a school id is needed
                results: [{
                    school_id: Optional[str]
                        School id if needed
                    email: str
                        Student email
                    assignments: [{
                        n_completed: Optional[int]
                            Number of completed questions
                        n_correct: Optional[int]
                            Number of correct questions
                    }]
                }]
            }
        If assignment gradebook wanted
            {
                group: str
                    Title of the group
                assignment: str
                    Title of the assignment
                questions: List[str]
                    Question title
                school_id_needed: bool
                    If a school id is needed
                results: [{
                    school_id: Optional[str]
                        School id if needed
                    email: str
                        Student email
                    questions: List[Optional[float]]
                        Grade for each question
                }]
            }

    Raises
    ------
    StudentGroup.DoesNotExist
        When the group pk doesn't correspond to an existing group
    StudentGroupAssignment.DoesNotExist
        When the assignment pk doesn't correspond to an existing group
    """
    group = StudentGroup.objects.get(pk=group_pk)

    if assignment_pk is not None:
        assignment = StudentGroupAssignment.objects.get(pk=assignment_pk)
    else:
        assignment = None

    memberships = StudentGroupMembership.objects.filter(group=group).order_by(
        Lower("student__student__email")
    )

    if assignment is None:
        assignments = group.studentgroupassignment_set.filter(
            distribution_date__isnull=False
        ).order_by("distribution_date")
        results = {
            "group": group.title,
            "assignments": [
                _assignment.assignment.identifier
                for _assignment in assignments
            ],
            "school_id_needed": group.student_id_needed,
            "results": [
                {
                    "school_id": membership.student_school_id
                    if group.student_id_needed
                    else None,
                    "email": membership.student.student.email,
                    "assignments": [
                        {
                            key: val
                            for key, val in _assignment.studentassignment_set.get(  # noqa
                                student=membership.student
                            ).results.items()
                            if key in ("n_completed", "n_correct")
                        }
                        if _assignment.studentassignment_set.filter(
                            student=membership.student
                        ).exists()
                        else None
                        for _assignment in assignments
                    ],
                }
                for membership in memberships
            ],
        }

    else:
        answers = Answer.objects.filter(assignment=assignment.assignment)
        questions = assignment.questions
        results = {
            "group": group.title,
            "assignment": assignment.assignment.title,
            "questions": [question.title for question in questions],
            "school_id_needed": group.student_id_needed,
            "results": [
                {
                    "school_id": membership.student_school_id
                    if group.student_id_needed
                    else None,
                    "email": membership.student.student.email,
                    "questions": [
                        answers.get(
                            question=question,
                            user_token=membership.student.student.username,
                        ).grade
                        if answers.filter(
                            question=question,
                            user_token=membership.student.student.username,
                        ).exists()
                        else None
                        for question in questions
                    ],
                }
                for membership in memberships
            ],
        }

    return results


def convert_gradebook_to_csv(results):
    """
    Converts the gradebook results to a csv generator.
    Parameters
    ----------
    results : Dict[str, Any]
        Either
            If group gradebook
                {
                    group: str
                        Title of the group
                    assignments: List[str]
                        Assignment identifier
                    school_id_needed: bool
                        If a school id is needed
                    results: [{
                        school_id: Optional[str]
                            School id if needed
                        email: str
                            Student email
                        assignments: [{
                            n_completed: Optional[int]
                                Number of completed questions
                            n_correct: Optional[int]
                                Number of correct questions
                        }]
                    }]
                }
            If assignment gradebook
                {
                    group: str
                        Title of the group
                    assignment: str
                        Title of the assignment
                    questions: List[str]
                        Question title
                    school_id_needed: bool
                        If a school id is needed
                    results: [{
                        school_id: Optional[str]
                            School id if needed
                        email: str
                            Student email
                        questions: List[Optional[float]]
                            Grade for each question
                    }]
                }

    Returns
    -------
    Iterator[str]
        First call:
            column names
        Other calls:
            each row of the csv
    """
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    if "assignment" in results:
        header = (
            (["Student ID"] if results["school_id_needed"] else [])
            + ["Student Email"]
            + results["questions"]
        )
        yield writer.writerow(header)

        for student in results["results"]:
            row = (
                ([student["school_id"]] if results["school_id_needed"] else [])
                + [student["email"]]
                + [
                    "-" if question is None else question
                    for question in student["questions"]
                ]
            )
            yield writer.writerow(row)

    else:
        header = (
            (["Student ID"] if results["school_id_needed"] else [])
            + ["Student Email"]
            + [
                "{} - {}".format(n, assignment)
                for assignment in results["assignments"]
                for n in ("n_correct", "n_completed")
            ]
        )
        yield writer.writerow(header)

        for student in results["results"]:
            row = (
                ([student["school_id"]] if results["school_id_needed"] else [])
                + [student["email"]]
                + [
                    "-" if assignment[n] is None else str(assignment[n])
                    for assignment in student["assignments"]
                    for n in ("n_correct", "n_completed")
                ]
            )
            yield writer.writerow(row)
