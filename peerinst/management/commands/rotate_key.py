import os
import re
import secrets
import string
from typing import Optional, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand

from peerinst import students
from peerinst.models import Student


class Command(BaseCommand):
    help = (
        "Changes the key. If rotating the password key, will change "
        "every student's password."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("key", choices=("secret", "token", "password"))

    def handle(self, *args, **options) -> None:
        key = options["key"]

        print(f"[*] Rotating {key.upper()}_KEY", end="\r")

        if key in ("secret", "token"):
            change_key(key)
        elif key == "password":
            new_key, old_key = change_key(key)
            if old_key is None:
                old_key = settings.SECRET_KEY
            n_students = Student.objects.count()
            for i, student in enumerate(Student.objects.iterator()):
                if student.student.check_password(
                    students.generate_password(
                        student.student.username, old_key
                    )
                ):
                    student.student.set_password(
                        students.generate_password(
                            student.student.username, new_key
                        )
                    )
                    student.student.save()
                print(
                    "[*] Updating students ({{:>{}}}/{{}})".format(
                        len(str(n_students))
                    ).format(i + 1, n_students),
                    end="\r",
                )
        else:
            raise NotImplementedError(
                "The command hasn't been implemented for that key type yet."
            )

        print(f"[+] Rotated {key.upper()}_KEY".ljust(80))


def change_key(key: str) -> Tuple[str, Optional[str]]:
    settings_path = os.path.join(
        os.path.dirname(__file__),
        os.pardir,
        os.pardir,
        os.pardir,
        "dalite",
        "settings.py",
    )
    local_settings_path = os.path.join(
        os.path.dirname(__file__),
        os.pardir,
        os.pardir,
        os.pardir,
        "dalite",
        "local_settings.py",
    )
    path = (
        local_settings_path
        if os.path.exists(local_settings_path)
        else settings_path
    )

    with open(path, "r") as f:
        lines = []
        modify_line = False
        previous_key = None
        for line in f:
            if modify_line:
                if line.startswith(")"):
                    modify_line = False
                else:
                    previous_key = re.match(  # type: ignore
                        r'^\s*"(.+)"$', line
                    ).group(1)
                    new_key = generate_password(64)
                    if len(f'{key.upper()}_KEY = "{new_key}"') > 79:
                        lines.append(f"{key.upper()}_KEY = (\n")
                        lines.append(f'    "{new_key}"\n')
                        lines.append(")\n")
                    else:
                        lines.append(f"{key.upper()}_KEY = " f'"{new_key}"\n')
            elif line.startswith(f"{key.upper()}_KEY ="):
                if "(" in line:
                    modify_line = True
                else:
                    previous_key = re.match(  # type: ignore
                        f'{key.upper()}_KEY\\s?=\\s?"(.+)"$', line
                    ).group(1)
                    new_key = generate_password(64)
                    if len(f'{key.upper()}_KEY = "{new_key}"') > 79:
                        lines.append(f"{key.upper()}_KEY = (\n")
                        lines.append(f'    "{new_key}"\n')
                        lines.append(")\n")
                    else:
                        lines.append(f"{key.upper()}_KEY = " f'"{new_key}"\n')
            else:
                lines.append(line)
        if previous_key is None:
            new_key = generate_password(64)
            if len(f'{key.upper()}_KEY = "{new_key}"') > 79:
                lines.append(f"{key.upper()}_KEY = (\n")
                lines.append(f'    "{new_key}"\n')
                lines.append(")\n")
            else:
                lines.append(f"{key.upper()}_KEY = " f'"{new_key}"\n')
    with open(path, "w") as f:
        for line in lines:
            f.write(line)

    return new_key, previous_key


def generate_password(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
