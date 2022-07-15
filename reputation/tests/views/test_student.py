import json

from peerinst.models import Student
from peerinst.tests.fixtures import *  # noqa
from reputation.tests.fixtures import *  # noqa
from reputation.views.student import (
    student_reputation as student_reputation_view,
)


def test_student_reputation(rf, student_reputation, student):
    data = {"id": student.pk}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = student.student

    resp = student_reputation_view(req)

    reputation, details = student_reputation.evaluate()

    assert resp.status_code == 200
    assert json.loads(resp.content.decode()) == {
        "reputation": reputation,
        "reputations": details,
    }


def test_student_reputation__new_reputation(rf, student):
    data = {"id": student.pk}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = student.student

    resp = student_reputation_view(req)

    student.refresh_from_db()
    reputation, details = student.reputation.evaluate()

    assert resp.status_code == 200
    assert json.loads(resp.content.decode()) == {
        "reputation": reputation,
        "reputations": details,
    }


def test_student_reputation__missing_params(rf, student_reputation, student):
    data = {}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = student.student

    resp = student_reputation_view(req)

    reputation, details = student_reputation.evaluate()

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_student_reputation__wrong_id(rf, student_reputation, student):
    data = {"id": student.pk}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = student.student
    Student.objects.get(pk=student.pk).delete()

    resp = student_reputation_view(req)

    reputation, details = student_reputation.evaluate()

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_student_reputation__other_student(rf, student_reputation, students):
    data = {"id": students[0].pk}
    req = rf.post("/test", json.dumps(data), content_type="application/json")
    req.user = students[1].student

    resp = student_reputation_view(req)

    reputation, details = student_reputation.evaluate()

    assert resp.status_code == 403
    assert resp.template_name == "403.html"
