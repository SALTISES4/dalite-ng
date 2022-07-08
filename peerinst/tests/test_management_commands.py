import os
from unittest import mock

from django.core.management import call_command
from django.db.utils import DatabaseError
from django.test import TestCase

devnull = open(os.devnull, "w")


@mock.patch(
    "sys.stdout", devnull
)  # Get rid of output this command prints to user
class SanityCheckTest(TestCase):
    def test_sanity_check_command_positive(self):
        call_command("sanity_check")

    def test_sanity_check_negative(self):
        # We want to check if this command fails if there is
        # any connection error to the database, so we are patching
        # cursor() call
        with mock.patch(
            "django.db.connection.cursor", side_effect=DatabaseError()
        ):
            with self.assertRaises(Exception):
                call_command("sanity_check")
