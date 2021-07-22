from django.contrib.auth.models import Permission, User
from django.core import mail
from django.urls import reverse

from peerinst.models import NewUserRequest
from quality.tests.fixtures import *  # noqa

from .. import factories


def test_index__superuser(client, superuser):
    assert client.login(username=superuser.username, password="test")
    resp = client.get(reverse("admin:index"))
    assert resp.status_code == 200


def test_index__staff(client, staff):
    assert client.login(username=staff.username, password="test")
    resp = client.get(reverse("admin:index"))
    assert resp.status_code == 302
    assert resp.url == "/en/admin/saltise/"


def test_new_user_approval_page(client, staff, new_user_requests):
    assert client.login(username=staff.username, password="test")
    resp = client.get(reverse("saltise-admin:new-user-approval"))
    assert "peerinst/saltise_admin/new_user_approval.html" in [
        t.name for t in resp.templates
    ]
    assert len(new_user_requests) == len(resp.context["new_users"])
    for req in new_user_requests:
        assert req.user.username in [
            u["username"] for u in resp.context["new_users"]
        ]

    for i, u in enumerate(resp.context["new_users"]):
        assert all(
            u_["date_joined"] <= u["date_joined"]
            for u_ in resp.context["new_users"][i + 1 :]
        )


def test_verify_user__approve(client, staff, new_user_requests):
    client.login(username=staff.username, password="test")
    user = new_user_requests[0].user
    assert not user.is_active

    resp = client.post(
        reverse("saltise-admin:verify-user"),
        {"username": user.username, "approve": True},
        content_type="application/json",
    )
    assert resp.status_code == 200

    user_ = User.objects.get(username=user.username)
    assert user_.is_active

    assert mail.outbox[0].subject == "Please verify your myDalite account"

    assert not NewUserRequest.objects.filter(user=user).exists()


def test_verify_user__refuse(client, staff, new_user_requests):
    client.login(username=staff.username, password="test")
    user = new_user_requests[0].user
    assert not user.is_active

    resp = client.post(
        reverse("saltise-admin:verify-user"),
        {"username": user.username, "approve": False},
        content_type="application/json",
    )
    assert resp.status_code == 200

    assert not User.objects.filter(username=user.username).exists()

    assert not mail.outbox

    assert not NewUserRequest.objects.filter(
        user__username=user.username
    ).exists()


def test_activity_page(client):
    saltise_staff = factories.UserFactory()
    saltise_staff.is_staff = True
    saltise_staff.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="peerinst",
            content_type__model="studentgroup",
            codename="view_studentgroup",
        )
    )
    saltise_staff.save()
    assert client.login(username=saltise_staff.username, password="test")
    resp = client.get(reverse("admin:peerinst_studentgroup_changelist"))

    assert resp.status_code == 200
