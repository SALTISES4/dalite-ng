from peerinst.forms import FirstAnswerForm


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
    assert "Please rephrase your rationale." in form.errors["rationale"]


def test_FirstAnswerForm_rationale_no_profanity_variants():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "Sh1tty rationale with bad a sneaky variant",
        },
    )

    assert len(form.errors) == 1
    assert "Please rephrase your rationale." in form.errors["rationale"]
