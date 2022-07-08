import random
import string
from math import exp
from operator import sub

import pytest

from quality.models.criterion.criterions.likelihood.model import create_model


@pytest.fixture
def english():
    return (
        "english",
        [
            "http://practicalcryptography.com/media/cryptanalysis/files/"
            "english_monograms.txt",
            "http://practicalcryptography.com/media/cryptanalysis/files/"
            "english_bigrams_1.txt",
            "http://practicalcryptography.com/media/cryptanalysis/files/"
            "english_trigrams.txt.zip",
        ],
        True,
    )


@pytest.fixture
def french():
    return (
        "french",
        [
            "http://practicalcryptography.com/media/cryptanalysis/files/"
            "french_monograms.txt",
            "http://practicalcryptography.com/media/cryptanalysis/files/"
            "french_bigrams_1.txt",
            "http://practicalcryptography.com/media/cryptanalysis/files/"
            "french_trigrams.txt.zip",
        ],
        True,
    )


def test_create_model(english, french):
    predict = create_model(*english)
    predict = create_model(*french)


def test_predict__english(english):
    test = (
        "It is a truth universally acknowledged, that a single man in "
        "possession of a good fortune, must be in want of a wife.",
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way.",
        "It was a bright cold day in April, and the clocks were striking "
        "thirteen.",
        "All children, except one, grow up.",
        "It was inevitable: the scent of bitter almonds always reminded him "
        "of the fate of unrequited love.",
        "Mother died today. Or maybe, yesterday; I can't be sure.",
        "All this happened, more or less.",
        "What are men to rocks and mountains?",
        "And so we beat on, boats against the current, borne back ceaselessly "
        "into the past.",
        "You have brains in your head. You have feet in your shoes. You can "
        "steer yourself any direction you choose. You're on your own. And you "
        "know what you know. And YOU are the one who'll decide where to go...",
        "All that is gold does not glitter, Not all those who wander are "
        "lost; The old that is strong does not wither, Deep roots are not "
        "reached by the frost.",
    )
    predict = create_model(*english)
    result = [1 - min(1, exp(-sub(*predict(t)))) for t in test]

    for r in result:
        assert r >= 0.95


def test_predict__english__random(english):
    test = tuple(
        "".join(
            random.choice([" "] + list(string.ascii_letters))
            for _ in range(random.randint(5, 50))
        )
        for _ in range(10)
    )
    predict = create_model(*english)
    result = [1 - min(1, exp(-sub(*predict(t)))) for t in test]

    for r in result:
        assert r < 0.95


def test_predict__french(french):
    test = (
        "Aujourd'hui, maman est morte. Ou peut-être hier, je ne sais pas. "
        "J'ai reçu un télégramme de l'asile : « Mère décédée. Enterrement "
        "demain. Sentiments distingués. » Cela ne veut rien dire. C'était "
        "peut-être hier.",
        "Lolita, lumière de ma vie, feu de mes reins. Mon péché, mon âme. "
        "Lo-li-ta : le bout de la langue fait trois petits bonds le long du "
        "palais pour venir, à trois, cogner contre les dents. Lo. Li. Ta.  "
        "Elle était Lo le matin, Lo tout court, un mètre quarante-huit en "
        "chaussettes, debout sur un seul pied. Elle était Lola en pantalon. "
        "Elle était Dolly à l'école. Elle était Dolorès sur le pointillé des "
        "formulaires. Mais dans mes bras, c'était toujours Lolita.",
        "Me voici donc seul sur la terre, n'ayant plus de frère, de prochain, "
        "d'ami, de société que moi-même.",
        "J’avais vingt ans. Je ne laisserai personne dire que c’est le plus "
        "bel âge de la vie.",
        "Les familles heureuses se ressemblent toutes; les familles "
        "malheureuses sont malheureuses chacune à leur façon.",
        "Je cherchais un endroit tranquille où mourir.",
    )
    predict = create_model(*french)
    result = [1 - min(1, exp(-sub(*predict(t)))) for t in test]

    for r in result:
        assert r >= 0.95


def test_predict__french__random(french):
    test = tuple(
        "".join(
            random.choice([" "] + list(string.ascii_letters))
            for _ in range(random.randint(5, 50))
        )
        for _ in range(10)
    )
    predict = create_model(*french)
    result = [1 - min(1, exp(-sub(*predict(t)))) for t in test]

    for r in result:
        assert r < 0.95


def test_predict__english__french(english, french):
    test = (
        "Aujourd'hui, maman est morte. Ou peut-être hier, je ne sais pas. "
        "J'ai reçu un télégramme de l'asile : « Mère décédée. Enterrement "
        "demain. Sentiments distingués. » Cela ne veut rien dire. C'était "
        "peut-être hier.",
        "Lolita, lumière de ma vie, feu de mes reins. Mon péché, mon âme. "
        "Lo-li-ta : le bout de la langue fait trois petits bonds le long du "
        "palais pour venir, à trois, cogner contre les dents. Lo. Li. Ta.  "
        "Elle était Lo le matin, Lo tout court, un mètre quarante-huit en "
        "chaussettes, debout sur un seul pied. Elle était Lola en pantalon. "
        "Elle était Dolly à l'école. Elle était Dolorès sur le pointillé des "
        "formulaires. Mais dans mes bras, c'était toujours Lolita.",
        "Me voici donc seul sur la terre, n'ayant plus de frère, de prochain, "
        "d'ami, de société que moi-même.",
        "J’avais vingt ans. Je ne laisserai personne dire que c’est le plus "
        "bel âge de la vie.",
        "Les familles heureuses se ressemblent toutes; les familles "
        "malheureuses sont malheureuses chacune à leur façon.",
        "Je cherchais un endroit tranquille où mourir.",
    )
    predict_english = create_model(*english)
    predict_french = create_model(*french)
    result = [
        1 - min(1, exp(predict_french(t)[0] - predict_english(t)[0]))
        for t in test
    ]

    for r in result:
        assert r < 0.95


def test_predict__french__english(french, english):
    test = (
        "It is a truth universally acknowledged, that a single man in "
        "possession of a good fortune, must be in want of a wife.",
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way.",
        "It was a bright cold day in April, and the clocks were striking "
        "thirteen.",
        "All children, except one, grow up.",
        "It was inevitable: the scent of bitter almonds always reminded him "
        "of the fate of unrequited love.",
        "Mother died today. Or maybe, yesterday; I can't be sure.",
        "All this happened, more or less.",
        "What are men to rocks and mountains?",
        "And so we beat on, boats against the current, borne back ceaselessly "
        "into the past.",
        "You have brains in your head. You have feet in your shoes. You can "
        "steer yourself any direction you choose. You're on your own. And you "
        "know what you know. And YOU are the one who'll decide where to go...",
        "All that is gold does not glitter, Not all those who wander are "
        "lost; The old that is strong does not wither, Deep roots are not "
        "reached by the frost.",
    )
    predict_english = create_model(*english)
    predict_french = create_model(*french)
    result = [
        1 - min(1, exp(predict_english(t)[0] - predict_french(t)[0]))
        for t in test
    ]

    for r in result:
        assert r < 0.95


def test_predict__english__1_gram(english):
    test = (
        "It is a truth universally acknowledged, that a single man in "
        "possession of a good fortune, must be in want of a wife.",
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way.",
        "It was a bright cold day in April, and the clocks were striking "
        "thirteen.",
        "All children, except one, grow up.",
        "It was inevitable: the scent of bitter almonds always reminded him "
        "of the fate of unrequited love.",
        "Mother died today. Or maybe, yesterday; I can't be sure.",
        "All this happened, more or less.",
        "What are men to rocks and mountains?",
        "And so we beat on, boats against the current, borne back ceaselessly "
        "into the past.",
        "You have brains in your head. You have feet in your shoes. You can "
        "steer yourself any direction you choose. You're on your own. And you "
        "know what you know. And YOU are the one who'll decide where to go...",
        "All that is gold does not glitter, Not all those who wander are "
        "lost; The old that is strong does not wither, Deep roots are not "
        "reached by the frost.",
    )
    predict = create_model(*english, max_gram=1)
    result = [1 - min(1, exp(-sub(*predict(t)))) for t in test]
    for r in result:
        assert r >= 0.95
