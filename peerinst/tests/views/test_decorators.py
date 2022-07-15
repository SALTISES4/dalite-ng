from django.contrib.auth.models import AnonymousUser

from peerinst.tests.fixtures import *  # noqa
from peerinst.views.decorators import student_required, teacher_required


def test_teacher_required__with_teacher(rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    fct = teacher_required(lambda req, teacher: teacher)
    resp = fct(req)
    assert resp == teacher


def test_teacher_required__with_student(rf, student):
    req = rf.get("/test")
    req.user = student.student

    fct = teacher_required(lambda req, teacher: teacher)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_teacher_required__with_teacher(rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    fct = teacher_required(lambda req, teacher: teacher)
    resp = fct(req)
    assert resp == teacher


def test_teacher_required__with_regular_user(rf, user):
    req = rf.get("/test")
    req.user = user

    fct = teacher_required(lambda req, teacher: teacher)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_teacher_required__with_anonymous_user(rf):
    req = rf.get("/test")
    req.user = AnonymousUser()

    fct = teacher_required(lambda req, teacher: teacher)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_student_required__with_student(rf, student):
    req = rf.get("/test")
    req.user = student.student

    fct = student_required(lambda req, student: student)
    resp = fct(req)
    assert resp == student


def test_student_required__with_teacher(rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    fct = student_required(lambda req, student: student)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_student_required__with_regular_user(rf, user):
    req = rf.get("/test")
    req.user = user

    fct = student_required(lambda req, student: student)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_student_required__with_anonymous_user(rf):
    req = rf.get("/test")
    req.user = AnonymousUser()

    fct = student_required(lambda req, student: student)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"
