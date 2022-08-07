import os
from functools import wraps

import celery
from celery import Celery
from celery.exceptions import OperationalError
from celery.schedules import crontab
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
    print(f"Request: {self.request!r}")


def try_async(func):
    """
    Decorator for celery tasks such that they default to synchronous operation
    if no workers are available
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info("Checking for celery message broker...")
            celery.current_app.control.ping()

        except OperationalError as e:
            info = "Celery unavailable ({}).  Executing {} synchronously.".format(  # noqa
                e, func.__name__
            )
            logger.info(info)
            return func(*args, **kwargs)

        else:
            logger.info("Checking for available workers...")
            available_workers = celery.current_app.control.inspect().active()

            if available_workers:
                info = "Celery workers available ({}).  Executing {} asynchronously.".format(  # noqa
                    list(available_workers.keys()), func.__name__
                )
                logger.info(info)
                return func.delay(*args, **kwargs)
            else:
                info = "No celery workers available.  Executing {} synchronously.".format(  # noqa
                    func.__name__
                )
                logger.info(info)
                return func(*args, **kwargs)

    return wrapper


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    app.conf.beat_schedule = {
        "clean_notifications": {
            "task": "peerinst.tasks.clean_notifications",
            "schedule": crontab(hour=0, minute=0),
        },
        "update_reputation_history": {
            "task": "reputation.tasks.update_reputation_history",
            "schedule": crontab(hour=0, minute=0),
        },
    }
