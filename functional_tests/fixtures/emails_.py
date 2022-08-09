import email
import os
from pathlib import Path

import pytest
from django.conf import settings


class SimpleMessage:
    """
    A very simple substitute for an EmailMessage
    """

    def __init__(self, message, *args, **kwargs):
        for key, value in message.items():
            if key.lower() == "to":
                self.to = value.strip().split(", ")
            elif key.lower() == "cc":
                self.cc = value.strip().split(", ")
            else:
                setattr(self, key.lower(), value)
        self.body = str(message.get_body(preferencelist=("plain",)))


class FileBasedOutbox:
    def __init__(self, *args, **kwargs):
        self.volume = Path(settings.EMAIL_FILE_PATH)

    def __len__(self):
        """
        Return count of files in email directory
        """
        count = 0
        for file in self.volume.iterdir():
            if file.is_file():
                count += 1
        return count

    def __getitem__(self, position):
        """
        Return file as a SimpleMessage based on position in time-sorted list
        (newest files first)
        """
        email_files = [
            file for file in self.volume.iterdir() if file.is_file()
        ]

        with sorted(
            email_files, key=lambda x: x.stat().st_mtime_ns, reverse=True
        )[position].open() as f:
            message = email.message_from_file(f, policy=email.policy.default)

        return SimpleMessage(message)

    def clear(self):
        """
        Clear the email directory
        """
        for file in self.volume.iterdir():
            if file.is_file():
                file.unlink()
        return


@pytest.fixture(scope="function")
def mail_outbox(mailoutbox):
    """
    Django uses the locmem email backend for testing that exposes an outbox
    which can be queried, cleared, etc.  The pytest-django fixture mailoutbox
    is a shortcut to the outbox attribute.

    Using a multi-container dockerized test environment means sent emails are
    on the process acting as host, not the process executing the functional
    test scripts.  The file-based email backend can be used to save emails to a
    shared network volume and accessed across processes, but we need to
    implement the outbox interface.
    """
    if not (staging_server := os.environ.get("STAGING_SERVER")):
        return mailoutbox
    print("Using staging server > replacing default mailoutbox fixture")
    outbox = FileBasedOutbox()
    yield outbox
    outbox.clear()
