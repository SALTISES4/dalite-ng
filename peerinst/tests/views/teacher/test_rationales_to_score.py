import json
from unittest import mock

import pytest
from django.http import HttpResponse
from django.urls import reverse

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


@pytest.mark.skip(reason="Only basic view implemented")
def test_rationales_to_score(client, teacher, answers, discipline):
    teacher.disciplines.add(discipline)
    for i, answer in enumerate(answers):
        answer.question.discipline = discipline
        answer.question.save()

    assert login_teacher(client, teacher)

    with mock.patch("peerinst.rationale_annotation.Quality") as Quality:
        qualities = [float(i) / len(answers) for i in range(len(answers))]
        Quality.objects.filter.return_value.exists.return_value = True
        Quality.objects.get.return_value.batch_evaluate.return_value = [
            (q, None) for q in qualities
        ]

        resp = client.post(
            reverse("teacher-dashboard--rationales"),
            json.dumps({}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = json.loads(resp.content.decode())
        assert len(data["rationales"]) == 5

        for a, a_ in zip(data["rationales"], answers[::-1]):
            assert a["id"] == a_.pk
            assert a["title"] == a_.question.title
            assert a["rationale"] == a_.rationale
            assert a["choice"] == a_.first_answer_choice
            assert (
                a["text"]
                == a_.question.answerchoice_set.all()[
                    a_.first_answer_choice - 1
                ].text
            )
            assert a["correct"] == a_.question.is_correct(
                a_.first_answer_choice
            )


@pytest.mark.skip(reason="Only basic view implemented")
def test_rationales_to_score__with_params(
    client, teacher, answers, discipline
):
    teacher.disciplines.add(discipline)
    for i, answer in enumerate(answers):
        answer.question.discipline = discipline
        answer.question.save()

    assert login_teacher(client, teacher)

    with mock.patch("peerinst.rationale_annotation.Quality") as Quality:
        qualities = [float(i) / len(answers) for i in range(len(answers))]
        Quality.objects.filter.return_value.exists.return_value = True
        Quality.objects.get.return_value.batch_evaluate.return_value = [
            (q, None) for q in qualities
        ]

        resp = client.post(
            reverse("teacher-dashboard--rationales"),
            json.dumps({"n": 3}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = json.loads(resp.content.decode())
        assert len(data["rationales"]) == 3

        for a, a_ in zip(data["rationales"], answers[::-1]):
            assert a["id"] == a_.pk
            assert a["title"] == a_.question.title
            assert a["rationale"] == a_.rationale
            assert a["choice"] == a_.first_answer_choice
            assert (
                a["text"]
                == a_.question.answerchoice_set.all()[
                    a_.first_answer_choice - 1
                ].text
            )
            assert a["correct"] == a_.question.is_correct(
                a_.first_answer_choice
            )

        resp = client.post(
            reverse("teacher-dashboard--rationales"),
            json.dumps({"current": [a.pk for a in answers[-3:]]}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = json.loads(resp.content.decode())
        assert len(data["rationales"]) == 5

        for a, a_ in zip(data["rationales"], answers[:-3][::-1]):
            assert a["id"] == a_.pk
            assert a["title"] == a_.question.title
            assert a["rationale"] == a_.rationale
            assert a["choice"] == a_.first_answer_choice
            assert (
                a["text"]
                == a_.question.answerchoice_set.all()[
                    a_.first_answer_choice - 1
                ].text
            )
            assert a["correct"] == a_.question.is_correct(
                a_.first_answer_choice
            )

        resp = client.post(
            reverse("teacher-dashboard--rationales"),
            json.dumps({"n": 3, "current": [a.pk for a in answers[-3:]]}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = json.loads(resp.content.decode())
        assert len(data["rationales"]) == 3

        for a, a_ in zip(data["rationales"], answers[:-3][::-1]):
            assert a["id"] == a_.pk
            assert a["title"] == a_.question.title
            assert a["rationale"] == a_.rationale
            assert a["choice"] == a_.first_answer_choice
            assert (
                a["text"]
                == a_.question.answerchoice_set.all()[
                    a_.first_answer_choice - 1
                ].text
            )
            assert a["correct"] == a_.question.is_correct(
                a_.first_answer_choice
            )


@pytest.mark.skip(reason="Only basic view implemented")
def test_rationales_to_score__wrong_params(client, teacher):
    assert login_teacher(client, teacher)

    with mock.patch(
        "peerinst.views.teacher.get_json_params",
        return_value=HttpResponse("", status=400),
    ):
        resp = client.post(
            reverse("teacher-dashboard--rationales"),
            json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
