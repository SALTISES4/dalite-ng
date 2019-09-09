import logging

from django.contrib.auth.models import AnonymousUser
from django.template.response import TemplateResponse

from dalite.views.errors import (
    response_400,
    response_403,
    response_404,
    response_500,
)


def test_response_400(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")

    resp = response_400(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=True,
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 400
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_400__default_message(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_400(
        req, msg="test1", log=logger.warning, use_template=True
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 400
    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message
        == "400 error for user AnonymousUser on path /test."
    )


def test_response_400__no_template(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_400(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=False,
    )

    assert not isinstance(resp, TemplateResponse)
    assert resp.status_code == 400
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_403(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")

    resp = response_403(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=True,
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 403
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_403__default_message(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_403(
        req, msg="test1", log=logger.warning, use_template=True
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 403
    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message
        == "403 error for user AnonymousUser on path /test."
    )


def test_response_403__no_template(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_403(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=False,
    )

    assert not isinstance(resp, TemplateResponse)
    assert resp.status_code == 403
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_404(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")

    resp = response_404(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=True,
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 404
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_404__default_message(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_404(
        req, msg="test1", log=logger.warning, use_template=True
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 404
    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message
        == "404 error for user AnonymousUser on path /test."
    )


def test_response_404__no_template(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_404(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=False,
    )

    assert not isinstance(resp, TemplateResponse)
    assert resp.status_code == 404
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_500(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")

    resp = response_500(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=True,
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 500
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"


def test_response_500__default_message(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_500(
        req, msg="test1", log=logger.warning, use_template=True
    )

    assert isinstance(resp, TemplateResponse)
    assert resp.status_code == 500
    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message
        == "500 error for user AnonymousUser on path /test."
    )


def test_response_500__no_template(rf, caplog):
    logger = logging.getLogger("test")
    req = rf.get("/test")
    req.user = AnonymousUser()

    resp = response_500(
        req,
        msg="test1",
        logger_msg="test2",
        log=logger.warning,
        use_template=False,
    )

    assert not isinstance(resp, TemplateResponse)
    assert resp.status_code == 500
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "test2"
