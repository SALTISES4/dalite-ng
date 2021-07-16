from peerinst.grammar import basic_syntax


def test_capitalize_first_letter():
    corrected_text = basic_syntax("missing capital.")
    assert corrected_text[0].isupper()


def test_remove_leading_whitespace():
    corrected_text = basic_syntax(" \t\n\r\f\v    Leading whitespaces.")
    assert corrected_text == "Leading whitespaces."


def test_remove_trailing_whitespace():
    corrected_text = basic_syntax("Trailing whitespaces. \t\n\r\f\v    ")
    assert corrected_text == "Trailing whitespaces."


def test_end_with_punctuation():
    corrected_text = basic_syntax("Missing punctuation")
    assert corrected_text == "Missing punctuation."

    corrected_text = basic_syntax("Missing punctuation.")
    assert corrected_text == "Missing punctuation."

    corrected_text = basic_syntax("Missing punctuation!")
    assert corrected_text == "Missing punctuation!"

    corrected_text = basic_syntax("Missing punctuation?")
    assert corrected_text == "Missing punctuation?"


def test_combine_inner_newlines():
    corrected_text = basic_syntax("Multiple \n\n\nnew \r\r\r\r\n\r\nlines.")
    assert corrected_text == "Multiple.\nNew.\nLines."


def test_multi_sentence_paragraph():
    corrected_text = basic_syntax(
        "sentence one  \n\n\nSentence two. and sentence three \r\n\r\n"
    )
    assert corrected_text == "Sentence one.\nSentence two. And sentence three."
