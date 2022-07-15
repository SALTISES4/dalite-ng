import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

from .models import Student, Teacher
from .students import (
    get_old_lti_student_username_and_password,
    get_student_username_and_password,
)

logger = logging.getLogger("peerinst-auth")


def authenticate_student(request, email, user_id=None):
    """
    Authenticates the student either with the username, password created from
    the email and SECRET_KEY or with the old lti way using the user_id and
    PASSWORD_GENERATOR_NONCE.

    Parameters
    ----------
    email : str
        Student email
    user_id : str
        Id returned by the lti consummer

    Returns
    -------
    User
        User corresponding to the student
    bool
        If the user was authenticated using the lti way or not
    """
    username, password = get_student_username_and_password(email)

    if (
        User.objects.filter(username=username)
        .filter(username__contains=username)
        .exists()
    ):
        user = authenticate(request, username=username, password=password)
        if (
            user
            and not Teacher.objects.filter(user__email=email).exists()
            and not Student.objects.filter(student=user).exists()
        ):
            Student.objects.create(student=user)

        lti = False

    else:
        # old way of generating student login
        if user_id is None:
            user_id = email.split("@")[0]
        old_username, old_password = get_old_lti_student_username_and_password(
            user_id
        )

        if (
            User.objects.filter(username=old_username)
            .filter(username__contains=old_username)
            .exists()
        ):
            user = authenticate(
                request, username=old_username, password=old_password
            )
            if (
                user
                and not Teacher.objects.filter(user__email=email).exists()
                and not Student.objects.filter(student=user).exists()
            ):
                Student.objects.create(student=user)

            lti = True

        else:
            try:
                User.objects.create_user(
                    username=username, email=email, password=password
                )
                user = authenticate(
                    request, username=username, password=password
                )
                if (
                    user
                    and not Teacher.objects.filter(user__email=email).exists()
                ):
                    Student.objects.create(student=user)
                lti = False
            except IntegrityError as e:
                logger.error(
                    "IntegrityError creating user - assuming result of "
                    "race condition: %s",
                    e.message,
                )
                user = None
                lti = False

    if user is None:
        logger.error("The user couldn't be authenticated.")

    return user, lti
