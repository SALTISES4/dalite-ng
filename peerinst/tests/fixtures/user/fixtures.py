import pytest

from . import factories as f
from .generators import add_user_requests, add_users, new_users


@pytest.fixture
def user():
    return add_users(new_users(1))[0]


@pytest.fixture
def users():
    return add_users(new_users(4)[1:])


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
def superuser():
    user = add_users(new_users(1))[0]
    user.username = "superuser"
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def new_teacher():
    return f.TeacherFactory()


@pytest.fixture
def staff():
    user = add_users(new_users(1))[0]
    user.username = "staff"
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def new_user_requests(users):
    return add_user_requests(users)
