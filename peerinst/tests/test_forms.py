import pytest
from django.core.exceptions import ValidationError

from peerinst.forms import (
    FirstAnswerForm,
    NonStudentAuthenticationForm,
    TeacherPasswordResetForm,
)


def test_FirstAnswerForm_first_choice_answer_required():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={"rationale": "Sample rationale with enough words to pass"},
    )

    assert len(form.errors) == 1
    assert (
        "Please make sure to select an answer choice."
        in form.errors["first_answer_choice"]
    )


def test_FirstAnswerForm_rationale_required():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={"first_answer_choice": 1},
    )

    assert len(form.errors) == 1
    assert (
        "Please provide a rationale for your choice."
        in form.errors["rationale"]
    )


def test_FirstAnswerForm_rationale_empty_min_length_validator():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={"first_answer_choice": 1, "rationale": "   "},
    )

    assert len(form.errors) == 1
    assert (
        "Please provide a rationale for your choice."
        in form.errors["rationale"]
    )


def test_FirstAnswerForm_rationale_min_length_validator():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={"first_answer_choice": 1, "rationale": "Short answer"},
    )

    assert len(form.errors) == 1
    assert (
        "Please provide a more detailed rationale for your choice."
        in form.errors["rationale"]
    )


def test_FirstAnswerForm_rationale_no_profanity():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "F&cking rationale with bad words in it",
        },
    )

    assert len(form.errors) == 1
    assert (
        "The language filter has labeled this as possibly toxic or profane; please rephrase your rationale."
        in form.errors["rationale"]
    )


def test_FirstAnswerForm_rationale_profanity_false_positives():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "It is where all the PE is transformed to KE",
        },
    )

    assert len(form.errors) == 0


def test_FirstAnswerForm_rationale_profanity_false_positives_from_whitespace():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "It is where all they find all the fi-sh. It is a good spot.",
        },
    )

    assert len(form.errors) == 0


def test_FirstAnswerForm_rationale_no_profanity_variants():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "Sh1tty rationale with bad a sneaky variant",
        },
    )

    assert len(form.errors) == 1
    assert (
        "The language filter has labeled this as possibly toxic or profane; please rephrase your rationale."
        in form.errors["rationale"]
    )


def test_FirstAnswerForm_rationale_valid_language():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "asfds asd  asdjklasdlk  sdfas;dlk asdf;sd",
        },
    )

    assert len(form.errors) == 1
    assert "Please clarify what you've written." in form.errors["rationale"]


def test_FirstAnswerForm_rationale_all_numbers():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "1111",
        },
    )

    assert len(form.errors) == 1
    assert "Please clarify what you've written." in form.errors["rationale"]


def test_FirstAnswerForm_rationale_valid_language_equation():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "Je pense que la réponse est y = mx + b",
        },
    )

    assert len(form.errors) == 0


def test_FirstAnswerForm_french_not_profane():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "Puisque l'onde va vers la droite",
        },
    )

    assert len(form.errors) == 0


def test_FirstAnswerForm_rationale_html_entities():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "Je pense que la réponse est &#8749;",
        },
    )

    form.is_valid()

    assert (
        form.cleaned_data["rationale"] == "Je pense que la réponse est &#8749;"
    )


def test_FirstAnswerForm_rationale_strip_script_tags():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "<script>Je pense que la réponse est &#8749;</script>",
        },
    )

    form.is_valid()

    assert (
        form.cleaned_data["rationale"] == "Je pense que la réponse est &#8749;"
    )


def test_FirstAnswerForm_rationale_strip_anchor_tags():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "<a href='#'>Je pense que la réponse est &#8749;</a>",
        },
    )

    form.is_valid()

    assert (
        form.cleaned_data["rationale"] == "Je pense que la réponse est &#8749;"
    )


def test_FirstAnswerForm_rationale_escaped_unsafe_tags():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "&lt;script&gt;This has escaped unsafe tags in it&lt;/script&gt;",
        },
    )

    form.is_valid()

    assert (
        form.cleaned_data["rationale"]
        == "&lt;script&gt;This has escaped unsafe tags in it&lt;/script&gt;"
    )


def test_TeacherPasswordResetForm(students, teachers, staff, superuser):
    form = TeacherPasswordResetForm()

    for teacher in teachers:
        assert teacher.user in list(form.get_users(teacher.user.email))

    for student in students:
        assert not list(form.get_users(student.student.email))
        student.student.set_unusable_password()

    for student in students:
        assert not list(form.get_users(student.student.email))

    assert not list(form.get_users(staff.email))

    assert not list(form.get_users(superuser.email))


def test_NonStudentAuthenticationForm(student, teacher, staff, superuser):
    form = NonStudentAuthenticationForm()

    with pytest.raises(ValidationError):
        form.confirm_login_allowed(student.student)

    form.confirm_login_allowed(teacher.user)
    form.confirm_login_allowed(staff)
    form.confirm_login_allowed(superuser)

    teacher.user.is_active = False
    teacher.user.save()

    with pytest.raises(ValidationError):
        form.confirm_login_allowed(teacher.user)
