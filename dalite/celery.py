from __future__ import absolute_import, unicode_literals

import os

from functools import wraps
from celery import Celery
from celery.utils.log import get_logger

logger = get_logger("peerinst-scheduled")

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dalite.settings")

app = Celery("dalite")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


@app.task
def heartbeat():
    logger.info("Heartbeat check")


def try_async(func):
    """
    Decorator for celery tasks such that they default to synchronous operation
    if no workers are available
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info("Checking for celery message broker...")
            heartbeat.delay()

        except heartbeat.OperationalError as e:
            info = "Celery unavailable ({}).  Executing {} synchronously.".format(  # noqa
                e, func.__name__
            )
            logger.info(info)
            return func(*args, **kwargs)

        else:
            logger.info("Checking for available workers...")
            # FIXME - This method of checking does not work across servers
            available_workers = app.control.ping(timeout=0.4)

            # FIXME
            if True:
                info = "Celery workers available ({}).  Executing {} asynchronously.".format(  # noqa
                    available_workers, func.__name__
                )
                logger.info(info)
                return func.delay(*args, **kwargs)
            else:
                info = "No celery workers available ({}).  Executing {} synchronously.".format(  # noqa
                    available_workers, func.__name__
                )
                logger.info(info)
                return func(*args, **kwargs)

    return wrapper
