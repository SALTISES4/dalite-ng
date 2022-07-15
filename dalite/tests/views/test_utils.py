import json

from django.http import HttpResponse

from dalite.views.utils import get_json_params


def test_get_json_params(rf):
    data = {"arg1": 1, "arg2": 2, "opt_arg1": 3, "opt_arg2": 4}

    req = rf.post("/test", json.dumps(data), content_type="application/json")

    args = get_json_params(
        req,
        args=["arg1", "arg2"],
        opt_args=["opt_arg1", "opt_arg2", "opt_arg3"],
    )
    assert not isinstance(args, HttpResponse)
    args, opt_args = args

    assert data["arg1"] == args[0]
    assert data["arg2"] == args[1]
    assert data["opt_arg1"] == opt_args[0]
    assert data["opt_arg2"] == opt_args[1]
    assert opt_args[2] is None


def test_get_json_params__wrong_data(rf):
    data = {"arg1": 1, "arg2": 2}

    req = rf.post("/test", data)

    args = get_json_params(req, args=["arg1", "arg2"])
    assert isinstance(args, HttpResponse)


def test_get_json_params__missing_arg(rf):
    data = {"arg1": 1}

    req = rf.post("/test", json.dumps(data), content_type="application/json")

    args = get_json_params(req, args=["arg1", "arg2"])
    assert isinstance(args, HttpResponse)
