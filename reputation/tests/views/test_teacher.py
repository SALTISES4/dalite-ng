import json

from peerinst.tests.fixtures import *  # noqa
from reputation.tests.fixtures import *  # noqa
from reputation.views.teacher import (
    teacher_reputation as teacher_reputation_view,
)


def test_teacher_reputation(rf, teacher_reputation, teacher):
    data = {"id": teacher.pk}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = teacher.user

    resp = teacher_reputation_view(req)

    reputation, details = teacher_reputation.evaluate()

    assert resp.status_code == 200
    assert json.loads(resp.content.decode()) == {
        "reputation": reputation,
        "reputations": details,
    }


def test_teacher_reputation__new_reputation(rf, teacher):
    data = {"id": teacher.pk}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = teacher.user

    resp = teacher_reputation_view(req)

    teacher.refresh_from_db()
    reputation, details = teacher.reputation.evaluate()

    assert resp.status_code == 200
    assert json.loads(resp.content.decode()) == {
        "reputation": reputation,
        "reputations": details,
    }


def test_teacher_reputation__missing_params(rf, teacher_reputation, teacher):
    data = {}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = teacher.user

    resp = teacher_reputation_view(req)

    reputation, details = teacher_reputation.evaluate()

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_teacher_reputation__wrong_id(rf, teacher_reputation, teacher):
    data = {"id": 2}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = teacher.user

    resp = teacher_reputation_view(req)

    reputation, details = teacher_reputation.evaluate()

    assert resp.status_code == 400
    assert resp.template_name == "400.html"
