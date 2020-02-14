import os
import re

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command

from peerinst.students import generate_password


def test_rotate_key__token__local_settings(mocker):
    key = "__test__"
    data = [f'TOKEN_KEY = "{key}"', "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "token")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*TOKEN_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i + 1 == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        os.remove(path)


def test_rotate_key__token__settings(mocker):
    key = "__test__"
    data = [f'TOKEN_KEY = "{key}"', "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[0], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    if os.path.exists(test_paths[1]):
        os.remove(test_paths[1])

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "token")

    with open(test_paths[0], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*TOKEN_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i + 1 == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        if os.path.exists(path):
            os.remove(path)


def test_rotate_key__token__multiple_lines(mocker):
    key = "__test__"
    data = ["TOKEN_KEY = (", f'    "{key}"', ")", "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "token")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*TOKEN_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i + 3 == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        os.remove(path)


def test_rotate_key__token__doesnt_exist(mocker):
    key = "__test__"
    data = ["OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "token")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*TOKEN_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        os.remove(path)


def test_rotate_key__secret__local_settings(mocker):
    key = "__test__"
    data = [f'SECRET_KEY = "{key}"', "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "secret")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*SECRET_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i + 1 == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        os.remove(path)


def test_rotate_key__secret__settings(mocker):
    key = "__test__"
    data = [f'SECRET_KEY = "{key}"', "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[0], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    if os.path.exists(test_paths[1]):
        os.remove(test_paths[1])

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "secret")

    with open(test_paths[0], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*SECRET_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i + 1 == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        if os.path.exists(path):
            os.remove(path)


def test_rotate_key__secret__multiple_lines(mocker):
    key = "__test__"
    data = ["SECRET_KEY = (", f'    "{key}"', ")", "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "secret")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*SECRET_KEY\s?=\s?"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            else:
                assert line.strip() in data
        assert i + 3 == len(data)

    assert key != key_
    assert len(key_) == 64

    for path in test_paths:
        os.remove(path)


def test_rotate_key__password__local_settings(mocker, students):
    key = settings.SECRET_KEY
    data = [f'PASSWORD_KEY = "{key}"', "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            ),
            User,
        )

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "password")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            elif not line.strip().startswith(
                ")"
            ) and not line.strip().endswith("("):
                assert line.strip() in data
        assert i + 1 == len(data) + 2

    assert key != key_
    assert len(key_) == 64

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key_),
            ),
            User,
        )
        assert (
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            )
            is None
        )

    for path in test_paths:
        os.remove(path)


def test_rotate_key__password__settings(mocker, students):
    key = settings.SECRET_KEY
    data = [f'PASSWORD_KEY = "{key}"', "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[0], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    if os.path.exists(test_paths[1]):
        os.remove(test_paths[1])

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            ),
            User,
        )

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "password")

    with open(test_paths[0], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            elif not line.strip().startswith(
                ")"
            ) and not line.strip().endswith("("):
                assert line.strip() in data
        assert i + 1 == len(data) + 2

    assert key != key_
    assert len(key_) == 64

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key_),
            ),
            User,
        )
        assert (
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            )
            is None
        )

    for path in test_paths:
        if os.path.exists(path):
            os.remove(path)


def test_rotate_key__password__multiple_lines(mocker, students):
    key = settings.SECRET_KEY
    data = ["PASSWORD_KEY = (", f'    "{key}"', ")", "OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            ),
            User,
        )

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "password")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            elif not line.strip().startswith(
                ")"
            ) and not line.strip().endswith("("):
                assert line.strip() in data
        assert i + 1 == len(data)

    assert key != key_
    assert len(key_) == 64

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key_),
            ),
            User,
        )
        assert (
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            )
            is None
        )

    for path in test_paths:
        os.remove(path)


def test_rotate_key__password__doesnt_exist(mocker, students):
    key = settings.SECRET_KEY
    data = [f'PASSWORD_KEY = "{key}"']
    data = ["OTHER_PARAM = 1"]
    test_paths = [
        os.path.abspath(os.path.join(os.sep, "tmp", "settings.py")),
        os.path.abspath(os.path.join(os.sep, "tmp", "local_settings.py")),
    ]
    with open(test_paths[1], "w") as f:
        for line in data:
            f.write(f"{line}\n")

    with open(test_paths[0], "w") as f:
        pass

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            ),
            User,
        )

    path_gen = iter(test_paths)
    mocker.patch(
        "peerinst.management.commands.rotate_key.os.path.join",
        side_effect=lambda *args: next(path_gen)
        if args[-2] == "dalite"
        else os.sep.join(args),
    )

    call_command("rotate_key", "password")

    with open(test_paths[1], "r") as f:
        for i, line in enumerate(f):
            match = re.match(r'^\s*"([^"]+)"$', line)
            if match is not None:
                key_ = match.group(1)
            elif not line.strip().startswith(
                ")"
            ) and not line.strip().endswith("("):
                assert line.strip() in data
        assert i == len(data) + 2

    assert key != key_
    assert len(key_) == 64

    for student in students:
        assert isinstance(
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key_),
            ),
            User,
        )
        assert (
            authenticate(
                username=student.student.username,
                password=generate_password(student.student.username, key),
            )
            is None
        )

    for path in test_paths:
        os.remove(path)
