import logging
import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Student
from .students import (
    get_old_lti_student_username_and_password,
    get_student_username_and_password,
)

logger = logging.getLogger(__name__)


def authenticate_student(email):

    err = None

    username, password = get_student_username_and_password(email)

    if User.objects.filter(username=username).exists():
        user = authenticate(username=username, password=password)
        if not Student.objects.filter(student=user).exists():
            Student.objects.create(student=user)

    else:
        # old way of generating student login
        user_id = "@".join(email.split("@")[:-1])
        old_username, old_password = get_old_lti_student_username_and_password(
            user_id
        )

        if User.objects.filter(username=old_username).exists():
            user = authenticate(username=old_username, password=old_password)
            if not Student.objects.filter(student=user).exists():
                Student.objects.create(student=user)

        else:
            try:
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                Student.objects.create(student=user)
            except IntegrityError as e:
                logger.info(
                    "IntegrityError creating user - assuming result of "
                    "race condition: %s",
                    e.message,
                )
                err = (
                    "IntegrityError creating user - assuming result of "
                    "race condition: {}".format(e.message)
                )
                user = None

    if user is None:
        logger.error("The user couldn't be authenticated.")
        err = "The user couldn't be authenticated."

    return err
