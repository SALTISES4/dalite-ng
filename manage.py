#!/usr/bin/env python
import os
import sys
from pathlib import Path


def check_mismatches(name):
    path = str(Path(__file__).parent / "requirements" / f"{name}.txt")
    return len(pip_lock.get_mismatches(path))


try:
    # Support PyMySQL
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dalite.settings")

    from django.core.management import execute_from_command_line

    try:
        import pip_lock
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Couldn't import pip-lock. Are you in the right virtualenv and up "
            + "to date?"
        ) from e

    # Should always have one of dev OR prod requirements
    requirements = [
        "requirements-dev",
        "requirements-test",
        "requirements-prod-aws",
    ]

    venv_check = list(map(check_mismatches, requirements))
    if min(venv_check) > 0:
        pip_lock.print_errors(
            [
                f"Environment does not match {' or '.join(requirements)} "
                + "requirements files",
                "Do you need to run pip-sync?",
            ]
        )
        sys.exit(1)

    execute_from_command_line(sys.argv)
