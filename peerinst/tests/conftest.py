import pytest
from django.conf import settings

from .fixtures import *  # noqa


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="session")
def celery_config():
    setattr(settings, "CELERY_BROKER_URL", "memory://")
    setattr(settings, "CELERY_RESULT_BACKEND", "cache+memory://")
    return {"broker_url": "memory://", "result_backend": "cache+memory://"}


def celery_config(redis_proc):
    redis_server = "redis://localhost:{}/0".format(redis_proc.port)
    setattr(settings, "CELERY_BROKER_URL", redis_server)
    setattr(settings, "CELERY_RESULT_BACKEND", redis_server)
    return {"broker_url": redis_server, "result_backend": redis_server}
