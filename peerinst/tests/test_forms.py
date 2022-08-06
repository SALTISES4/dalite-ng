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
    assert (
        "The language filter has labeled this as possibly toxic or profane; please rephrase your rationale."
        in form.errors["rationale"]
    )


def test_FirstAnswerForm_rationale_profanity_safewords():
    form = FirstAnswerForm(
        answer_choices=["A. Choice A", "B. Choice B"],
        data={
            "first_answer_choice": 1,
            "rationale": "It is where all the PE is transformed to KE",
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
