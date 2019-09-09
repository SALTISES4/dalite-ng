from django.core.urlresolvers import reverse

from peerinst.models import AnswerAnnotation
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_evaluate_rationale(client, teacher, answers):
    answer = answers[0]

    assert login_teacher(client, teacher)

    n = AnswerAnnotation.objects.count()

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"),
        {"id": answer.pk, "score": 0},
        follow=True,
    )

    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/teacher/cards/rationale_to_score_card.html"
        for t in resp.templates
    )
    assert AnswerAnnotation.objects.count() == n + 1


def test_evaluate_rationale__missing_params(client, teacher, answers):
    answer = answers[0]

    assert login_teacher(client, teacher)

    n = AnswerAnnotation.objects.count()

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"), {"id": answer.pk}
    )

    assert resp.status_code == 400
    assert AnswerAnnotation.objects.count() == n

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"), {"score": 0}
    )

    assert resp.status_code == 400
    assert AnswerAnnotation.objects.count() == n

    resp = client.post(reverse("teacher-dashboard--evaluate-rationale"), {})

    assert resp.status_code == 400
    assert AnswerAnnotation.objects.count() == n


def test_evaluate_rationale__wrong_answer_pk(client, teacher):
    assert login_teacher(client, teacher)

    n = AnswerAnnotation.objects.count()

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"), {"id": 0, "score": 0}
    )

    assert resp.status_code == 400
    assert AnswerAnnotation.objects.count() == n


def test_evaluate_rationale__wrong_score(client, teacher, answers):
    answer = answers[0]

    assert login_teacher(client, teacher)

    n = AnswerAnnotation.objects.count()

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"),
        {"id": answer.pk, "score": 4},
    )

    assert resp.status_code == 400
    assert AnswerAnnotation.objects.count() == n

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"),
        {"id": answer.pk, "score": -1},
    )

    assert resp.status_code == 400
    assert AnswerAnnotation.objects.count() == n
