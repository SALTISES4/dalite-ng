import logging
import re

# import bleach

# import contextualSpellCheck
# import editdistance
# import spacy

logger = logging.getLogger("nlp")
# nlp = spacy.load("en_core_web_sm")
# contextualSpellCheck.add_to_pipe(nlp)


# def spell_check(text):
#     logger.debug(text)
#     output = []
#     doc = nlp(bleach.clean(text, tags=[], strip=True))
#     for sentence in doc.sents:
#         _sentence = str(sentence).strip()
#         for suggestion in doc._.suggestions_spellCheck.items():
#             misspell, correction = suggestion
#             if (
#                 editdistance.distance(str(misspell), str(correction)) < 3
#                 and len(str(misspell)) > 2
#                 and str(misspell).isalpha()
#             ):
#                 _sentence = _sentence.replace(str(misspell), str(correction))
#
#         output.append(
#             f"{_sentence[0].upper()}{_sentence[1:]}"
#             if len(_sentence) > 1
#             else _sentence
#         )
#
#     processed_text = " ".join(output)
#     if processed_text and processed_text[-1] not in ".?!":
#         processed_text += "."
#
#     logger.debug(processed_text)
#
#     return processed_text


def basic_syntax(text):
    """
    For text:
    - Remove leading whitespace.
    - Remove trailing whitespace.
    - Combine multiple new lines/line returns into one within text.

    For each sentence:
    - Start with a capital letter.
    - End with a punctuation mark.
    """
    # logger.debug(text)
    _text = re.sub(r"[\n|\r][\n|\r]+", "\n", text.strip())
    if len(_text) > 1:
        processed_text = []
        for p in _text.split("\n"):
            processed_paragraph = []
            for s in re.split(r"[.|!|?]\s+", p.strip()):
                _s = s.strip()
                if len(_s) > 1:
                    processed_paragraph.append(
                        f"{_s[0].upper()}{_s[1:]}{'' if s[-1] in '.?!:;' else '.'}"  # noqa E501
                    )
                else:
                    processed_paragraph.append(_s)
            processed_text.append(" ".join(processed_paragraph))

        output = "\n".join(processed_text)
        # logger.debug(output)
        return output
    return _text
