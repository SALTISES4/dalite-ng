# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AnonymousUser

from peerinst.tests.fixtures import *  # noqa
from reputation.views.decorators import (
    logged_in_non_student_required,
    student_required,
)


def test_logged_in_non_student_required__with_student(rf, student):
    req = rf.get("/test")
    req.user = student.student

    fct = logged_in_non_student_required(lambda req: req.user)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_logged_in_non_student_required__with_teacher(rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    fct = logged_in_non_student_required(lambda req: req.user)
    resp = fct(req)
    assert resp == teacher.user


def test_logged_in_non_student_required__with_regular_user(rf, user):
    req = rf.get("/test")
    req.user = user

    fct = logged_in_non_student_required(lambda req: req.user)
    resp = fct(req)
    assert resp == user


def test_logged_in_non_student_required__with_anonymous_user(rf):
    req = rf.get("/test")
    req.user = AnonymousUser()

    fct = logged_in_non_student_required(lambda req: req.user)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_student_required__with_student(client, rf, student):
    req = rf.get("/test")
    req.user = student.student

    fct = student_required(lambda req: req.user)
    resp = fct(req)
    assert resp == student.student


def test_student_required__with_teacher(client, rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    fct = student_required(lambda req: req.user)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_student_required__with_regular_user(client, rf, user):
    req = rf.get("/test")
    req.user = user

    fct = student_required(lambda req: req.user)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_student_required__with_anonymous_user(client, rf, user):
    req = rf.get("/test")
    req.user = AnonymousUser()

    fct = student_required(lambda req: req.user)
    resp = fct(req)
    assert resp.status_code == 403
    assert resp.template_name == "403.html"
