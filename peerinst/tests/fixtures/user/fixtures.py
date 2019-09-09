import pytest

from . import factories as f
from .generators import add_users, new_users


@pytest.fixture
def user():
    return add_users(new_users(1))[0]


@pytest.fixture
def new_user():
    return f.UserFactory()


@pytest.fixture
def admin():
    return f.UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def inactive_user():
    return f.UserFactory(is_active=False)


@pytest.fixture
def new_teacher():
    return f.TeacherFactory()
