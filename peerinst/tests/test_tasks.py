from unittest import mock

import pytest
from celery.result import AsyncResult

from peerinst.tasks import compute_gradebook_async, send_mail_async
from peerinst.tests.fixtures import *  # noqa


@pytest.mark.skip(reason="Can't run multiple celery workers")
def test_send_mail_async(celery_worker):
    args = [1, 2, 3]
    kwargs = {"a": 1, "b": 2, "c": 3}
    with mock.patch("peerinst.tasks.send_mail") as send_mail:
        result = send_mail_async(*args, **kwargs)
        assert isinstance(result, AsyncResult)
        send_mail.called_with(*args, **kwargs)


@pytest.mark.skip(reason="Can't run multiple celery workers")
def test_send_mail_async__celery_not_running():
    args = [1, 2, 3]
    kwargs = {"a": 1, "b": 2, "c": 3}
    with mock.patch("peerinst.tasks.send_mail") as send_mail:
        result = send_mail_async(*args, **kwargs)
        assert not isinstance(result, AsyncResult)
        send_mail.called_with(*args, **kwargs)


@pytest.mark.skip(reason="Can't run multiple celery workers")
def test_compute_gradebook_async(celery_worker):
    group_pk = 1
    assignment_pk = 1
    gradebook = mock.MagicMock()
    gradebook.compute_gradebook.return_value = True
    with mock.patch.dict("sys.modules", {"peerinst.gradebook": gradebook}):
        result = compute_gradebook_async(group_pk, assignment_pk)
        assert isinstance(result, AsyncResult)
        gradebook.compute_gradebook.called_with(group_pk, assignment_pk)


@pytest.mark.skip(reason="Can't run multiple celery workers")
def test_compute_gradebook_async__celery_not_running():
    group_pk = 1
    assignment_pk = 1
    gradebook = mock.MagicMock()
    gradebook.compute_gradebook.return_value = True
    with mock.patch.dict("sys.modules", {"peerinst.gradebook": gradebook}):
        result = compute_gradebook_async(group_pk, assignment_pk)
        assert not isinstance(result, AsyncResult)
        gradebook.compute_gradebook.called_with(group_pk, assignment_pk)
