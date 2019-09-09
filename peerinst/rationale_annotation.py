# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from operator import itemgetter

from django.db.models import Count, Q

from quality.models import Quality

from .models import Answer, AnswerAnnotation, Question, Teacher


def choose_questions(teacher):
    """
    Selects subset of questions that are relevant to teacher interests
    """

    question_list = Question.unflagged_objects.all().order_by("-created_on")

    if len(teacher.disciplines.all()) > 0:
        question_list = question_list.filter(
            discipline__in=teacher.disciplines.all()
        ).exclude(teacher=teacher)
    if len(teacher.favourite_questions.all()) > 0:
        question_list = question_list.exclude(
            pk__in=teacher.favourite_questions.all()
        )
    return question_list


def choose_rationales(teacher, n=5):
    """
    Evaluates each rationale based on if the `teacher` should evaluate and
    returns the top `n` ones.

    Parameters
    ----------
    teacher : Teacher
        Teacher for whom the rationales should be chosen
    n : int (default : 5)
        Number of answers to return

    Returns
    -------
    List[Answer]
        Rationales for the teacher to evaluate
    """
    assert isinstance(teacher, Teacher), "Precondition failed for `teacher`"
    assert isinstance(n, int), "Precondition failed for `n`"

    answers = (
        Answer.objects.filter(
            question__discipline__in=teacher.disciplines.all()
        )
        .exclude(
            pk__in=AnswerAnnotation.objects.filter(
                annotator=teacher.user
            ).values_list("answer", flat=True)
        )
        .order_by("-datetime_first")
    )

    if not answers:
        return []

    if Quality.objects.filter(
        quality_type__type="global", quality_use_type__type="validation"
    ).exists():
        qualities = map(
            itemgetter(0),
            Quality.objects.get(
                quality_type__type="global",
                quality_use_type__type="validation",
            ).batch_evaluate(answers),
        )
        answers = [
            a
            for a, q in sorted(
                zip(answers, qualities), key=itemgetter(1), reverse=True
            )
        ]

    return answers[:n]


def choose_rationales_no_quality(teacher, n=5):
    """
    Evaluates each rationale based on if the `teacher` should evaluate and
    returns the top `n` ones.
    Filters for actual student answers that have resulted in students
    changing their mind, and ordered by those that have been shown often

    Parameters
    ----------
    teacher : Teacher
        Teacher for whom the rationales should be chosen
    n : int (default : 5)
        Number of answers to return

    Returns
    -------
    List[Answer]
        Rationales for the teacher to evaluate
    """
    assert isinstance(teacher, Teacher), "Precondition failed for `teacher`"
    assert isinstance(n, int), "Precondition failed for `n`"
    from .util import student_list_from_student_groups

    # if teacher has active students, sample from their most recent student
    # answers
    current_students = student_list_from_student_groups(
        group_list=teacher.current_groups.all()
    )

    # print(len(current_students)," current students")

    # if no current_students,or current students have no answers yet,
    # get previous students
    if (
        len(current_students) == 0
        or Answer.objects.filter(user_token__in=current_students).count() < n
    ):
        current_students.extend(
            student_list_from_student_groups(
                group_list=teacher.studentgroup_set.all()
            )
        )
    # print(len(current_students)," current students after extend into past")

    current_assignments = list(
        teacher.current_groups.values_list(
            "studentgroupassignment__assignment__identifier", flat=True
        )
    )

    # print(len(current_assignments)," current assignments")

    # if no current_assignments,or current assignments have no answers yet,
    # get previous assignments

    if (
        len(current_assignments) == 0
        or Answer.objects.filter(user_token__in=current_assignments).count()
        < n
    ):
        current_assignments.extend(teacher.assignments.all())

    # print(len(current_assignments),"
    # current assignments after extend into past")

    if len(current_assignments) > 0 and len(current_students) > n:
        convincing_rationales = (
            Answer.objects.filter(
                user_token__in=current_students,
                assignment_id__in=current_assignments,
            )
            .values("chosen_rationale")
            .annotate(times_chosen=Count("chosen_rationale"))
            .order_by("-times_chosen")
            .values_list("chosen_rationale", flat=True)
        )
    elif teacher.favourite_questions.all().count() > 0:
        # teacher new to dalite will have no students or assignments
        # first try if they have any favorite questions
        convincing_rationales = (
            Answer.objects.filter(
                question_id__in=teacher.favourite_questions.all(),
                second_answer_choice__isnull=False,
            )
            .values("chosen_rationale")
            .annotate(times_chosen=Count("chosen_rationale"))
            .order_by("-times_chosen")
            .values_list("chosen_rationale", flat=True)
        )
    elif teacher.disciplines.all().count() > 0:
        # if no favourite_questions, try based on disciplines
        convincing_rationales = (
            Answer.objects.filter(
                question_id__in=teacher.disciplines.all().values_list(
                    "question", flat=True
                ),
                second_answer_choice__isnull=False,
            )
            .values("chosen_rationale")
            .annotate(times_chosen=Count("chosen_rationale"))
            .order_by("-times_chosen")
            .values_list("chosen_rationale", flat=True)
        )

    else:
        # otherwise send nothing
        convincing_rationales = Answer.objects.none()

    # print(convincing_rationales.count(), " convincing_rationales")
    # print(convincing_rationales)

    # remove answers that have been scored twice already, or that
    # have been scored by the current users

    no_score_needed = (
        AnswerAnnotation.objects.filter(score__isnull=False)
        .annotate(times_scored=Count("answer"))
        .filter(Q(times_scored__gt=2) | Q(annotator=teacher.user))
        .values_list("answer", flat=True)
    )
    # print(no_score_needed.count(), " answers no score needed")
    # print(no_score_needed)
    #
    if convincing_rationales.count() > 0:
        answers = (
            Answer.objects.filter(pk__in=convincing_rationales).exclude(
                pk__in=no_score_needed
            )
            # .annotate(times_shown=Count("shown_answer"))
            # .order_by("-times_shown")
        )
        # print("****")
        # print(answers.values("pk","times_shown"))
    else:
        answers = convincing_rationales

    # print("final set:")
    # print(answers)

    return answers[:n]
