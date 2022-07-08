import pytest

from peerinst.gradebooks import compute_gradebook, convert_gradebook_to_csv
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.question import add_answers


def test_compute_gradebook__group__no_student_assignment(
    group, students, student_group_assignments
):
    gradebook = compute_gradebook(group.pk)
    assert gradebook["group"] == group.title
    assert "assignment" not in gradebook
    for assignment in student_group_assignments:
        assert assignment.assignment.identifier in gradebook["assignments"]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for assignment in student["assignments"]:
            assert assignment["n_completed"] is None
            assert assignment["grade"] is None


def test_compute_gradebook__group__no_student_assignment__student_id(
    group, students, student_group_assignments
):
    group.student_id_needed = True
    group.save()
    for i, student in enumerate(students):
        student.student_school_id = str(i)
        student.save()
    gradebook = compute_gradebook(group.pk)
    assert gradebook["group"] == group.title
    assert "assignment" not in gradebook
    for assignment in student_group_assignments:
        assert assignment.assignment.identifier in gradebook["assignments"]
    assert gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["email"] in [s.student.email for s in students]
        assert student["school_id"] == [
            s.student.email for s in students
        ].index(student["email"])
        for assignment in student["assignments"]:
            assert assignment["n_completed"] is None
            assert assignment["grade"] is None


def test_compute_gradebook__group__none_done(
    group, students, student_group_assignments, student_assignments
):
    gradebook = compute_gradebook(group.pk)
    assert gradebook["group"] == group.title
    assert "assignment" not in gradebook
    for assignment in student_group_assignments:
        assert assignment.assignment.identifier in gradebook["assignments"]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for assignment in student["assignments"]:
            assert assignment["n_completed"] == 0
            assert assignment["grade"] == 0


def test_compute_gradebook__group__all_correct(
    group, students, student_group_assignments, student_assignments
):
    for assignment in student_group_assignments:
        for assignment_ in assignment.studentassignment_set.all():
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=False,
                correct_second=False,
            )
    gradebook = compute_gradebook(group.pk)
    assert gradebook["group"] == group.title
    assert "assignment" not in gradebook
    for assignment in student_group_assignments:
        assert assignment.assignment.identifier in gradebook["assignments"]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for assignment, assignment_ in zip(
            student["assignments"], gradebook["assignments"]
        ):
            n = len(
                next(
                    a
                    for a in student_group_assignments
                    if a.assignment.identifier == assignment_
                ).questions
            )
            assert assignment["n_completed"] == n
            assert assignment["grade"] == 0


def test_compute_gradebook__group__all_correct(
    group, students, student_group_assignments, student_assignments
):
    for assignment in student_group_assignments:
        for assignment_ in assignment.studentassignment_set.all():
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=True,
                correct_second=True,
            )
    gradebook = compute_gradebook(group.pk)
    assert gradebook["group"] == group.title
    assert "assignment" not in gradebook
    for assignment in student_group_assignments:
        assert assignment.assignment.identifier in gradebook["assignments"]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for assignment, assignment_ in zip(
            student["assignments"], gradebook["assignments"]
        ):
            n = len(
                next(
                    a
                    for a in student_group_assignments
                    if a.assignment.identifier == assignment_
                ).questions
            )
            assert assignment["n_completed"] == n
            assert assignment["grade"] == n


def test_compute_gradebook__assignment__no_student_assignment(
    group, students, student_group_assignments
):
    assignment = student_group_assignments[0]
    gradebook = compute_gradebook(group.pk, assignment.pk)
    assert gradebook["group"] == group.title
    assert gradebook["assignment"] == assignment.assignment.title
    for question in gradebook["questions"]:
        assert question in [q.title for q in assignment.questions]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for question in student["questions"]:
            assert question is None


def test_compute_gradebook__assignment__no_student_assignment__student_id(
    group, students, student_group_assignments
):
    assignment = student_group_assignments[0]
    group.student_id_needed = True
    group.save()
    for i, student in enumerate(students):
        student.student_school_id = str(i)
        student.save()
    gradebook = compute_gradebook(group.pk, assignment.pk)
    assert gradebook["group"] == group.title
    assert gradebook["assignment"] == assignment.assignment.title
    for question in gradebook["questions"]:
        assert question in [q.title for q in assignment.questions]
    assert gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for question in student["questions"]:
            assert question is None
        assert student["school_id"] == [
            s.student.email for s in students
        ].index(student["email"])


def test_compute_gradebook__assignment__none_done(
    group, students, student_group_assignments, student_assignments
):
    assignment = student_group_assignments[0]
    gradebook = compute_gradebook(group.pk, assignment.pk)
    assert gradebook["group"] == group.title
    assert gradebook["assignment"] == assignment.assignment.title
    for question in gradebook["questions"]:
        assert question in [q.title for q in assignment.questions]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for question in student["questions"]:
            assert question is None


def test_compute_gradebook__assignment__none_correct(
    group, students, student_group_assignments, student_assignments
):
    assignment = student_group_assignments[0]
    for assignment_ in assignment.studentassignment_set.all():
        add_answers(
            student=assignment_.student,
            questions=assignment.questions,
            assignment=assignment.assignment,
            correct_first=False,
            correct_second=False,
        )
    gradebook = compute_gradebook(group.pk, assignment.pk)
    assert gradebook["group"] == group.title
    assert gradebook["assignment"] == assignment.assignment.title
    for question in gradebook["questions"]:
        assert question in [q.title for q in assignment.questions]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for question in student["questions"]:
            assert question == 0


def test_compute_gradebook__assignment__all_correct(
    group, students, student_group_assignments, student_assignments
):
    assignment = student_group_assignments[0]
    for assignment_ in assignment.studentassignment_set.all():
        add_answers(
            student=assignment_.student,
            questions=assignment.questions,
            assignment=assignment.assignment,
            correct_first=True,
            correct_second=True,
        )
    gradebook = compute_gradebook(group.pk, assignment.pk)
    assert gradebook["group"] == group.title
    assert gradebook["assignment"] == assignment.assignment.title
    for question in gradebook["questions"]:
        assert question in [q.title for q in assignment.questions]
    assert not gradebook["school_id_needed"]
    for student in gradebook["results"]:
        assert student["school_id"] is None
        assert student["email"] in [s.student.email for s in students]
        for question in student["questions"]:
            assert question == 1


def test_convert_gradebook_to_csv__group():
    n_assignments = 5
    n_students = 50
    results = {
        "group": "test",
        "assignments": ["assignment_" + str(i) for i in range(n_assignments)],
        "school_id_needed": False,
        "results": [
            {
                "school_id": None,
                "email": f"test{i}@test.com",
                "assignments": [
                    {"n_completed": j * 10 + i, "grade": j * 10 + i % 10}
                    for j in range(n_assignments)
                ],
            }
            for i in range(n_students)
        ],
    }
    csv_gen = convert_gradebook_to_csv(results)
    header = next(csv_gen)
    assert header == (
        "Student Email,"
        + ",".join(
            f"grade - assignment_{i},n_completed - assignment_{i}"
            for i in range(n_assignments)
        )
        + "\r\n"
    )
    for i in range(n_students):
        line = next(csv_gen)
        assert (
            line
            == f"test{i}@test.com,"
            + ",".join(
                f"{j * 10 + i % 10},{j * 10 + i}" for j in range(n_assignments)
            )
            + "\r\n"
        )
    with pytest.raises(StopIteration):
        next(csv_gen)


def test_convert_gradebook_to_csv__group__school_id():
    n_assignments = 5
    n_students = 50
    results = {
        "group": "test",
        "assignments": ["assignment_" + str(i) for i in range(n_assignments)],
        "school_id_needed": True,
        "results": [
            {
                "school_id": str(i),
                "email": f"test{i}@test.com",
                "assignments": [
                    {"n_completed": j * 10 + i, "grade": j * 10 + i % 10}
                    for j in range(n_assignments)
                ],
            }
            for i in range(n_students)
        ],
    }
    csv_gen = convert_gradebook_to_csv(results)
    header = next(csv_gen)
    assert header == (
        "Student ID,Student Email,"
        + ",".join(
            f"grade - assignment_{i},n_completed - assignment_{i}"
            for i in range(n_assignments)
        )
        + "\r\n"
    )
    for i in range(n_students):
        line = next(csv_gen)
        assert (
            line
            == f"{i},test{i}@test.com,"
            + ",".join(
                f"{j * 10 + i % 10},{j * 10 + i}" for j in range(n_assignments)
            )
            + "\r\n"
        )
    with pytest.raises(StopIteration):
        next(csv_gen)


def test_convert_gradebook_to_csv__assignment():
    n_assignments = 5
    n_students = 50
    results = {
        "group": "test",
        "assignment": "test",
        "questions": ["question_" + str(i) for i in range(n_assignments)],
        "school_id_needed": False,
        "results": [
            {
                "school_id": None,
                "email": f"test{i}@test.com",
                "questions": [j % 2 for j in range(n_assignments)],
            }
            for i in range(n_students)
        ],
    }
    csv_gen = convert_gradebook_to_csv(results)
    header = next(csv_gen)
    assert header == (
        "Student Email,"
        + ",".join(f"question_{i}" for i in range(n_assignments))
        + "\r\n"
    )
    for i in range(n_students):
        line = next(csv_gen)
        assert (
            line
            == f"test{i}@test.com,"
            + ",".join(str(j % 2) for j in range(n_assignments))
            + "\r\n"
        )
    with pytest.raises(StopIteration):
        next(csv_gen)


def test_convert_gradebook_to_csv__assignment__school_id():
    n_assignments = 5
    n_students = 50
    results = {
        "group": "test",
        "assignment": "test",
        "questions": ["question_" + str(i) for i in range(n_assignments)],
        "school_id_needed": True,
        "results": [
            {
                "school_id": str(i),
                "email": f"test{i}@test.com",
                "questions": [j % 2 for j in range(n_assignments)],
            }
            for i in range(n_students)
        ],
    }
    csv_gen = convert_gradebook_to_csv(results)
    header = next(csv_gen)
    assert header == (
        "Student ID,Student Email,"
        + ",".join(f"question_{i}" for i in range(n_assignments))
        + "\r\n"
    )
    for i in range(n_students):
        line = next(csv_gen)
        assert (
            line
            == f"{i},test{i}@test.com,"
            + ",".join(str(j % 2) for j in range(n_assignments))
            + "\r\n"
        )
    with pytest.raises(StopIteration):
        next(csv_gen)
