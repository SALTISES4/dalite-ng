import logging

import bleach
import contextualSpellCheck
import editdistance
import spacy

logger = logging.getLogger("nlp")
nlp = spacy.load("en_core_web_sm")
contextualSpellCheck.add_to_pipe(nlp)


def spell_check(text):
    logger.debug(text)
    output = []
    doc = nlp(bleach.clean(text, tags=[], styles=[], strip=True))
    for sentence in doc.sents:
        _sentence = str(sentence).strip()
        for suggestion in doc._.suggestions_spellCheck.items():
            misspell, correction = suggestion
            if (
                editdistance.distance(str(misspell), str(correction)) < 3
                and len(str(misspell)) > 2
                and str(misspell).isalpha()
            ):
                _sentence = _sentence.replace(str(misspell), str(correction))

        output.append(
            f"{_sentence[0].upper()}{_sentence[1:]}"
            if len(_sentence) > 1
            else _sentence
        )

    processed_text = " ".join(output)
    if processed_text and processed_text[-1] not in ".?!":
        processed_text += "."

    logger.debug(processed_text)

    return processed_text
