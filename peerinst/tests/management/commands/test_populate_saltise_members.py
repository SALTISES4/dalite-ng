import pytest
from django.core.management import call_command

from peerinst.models import SaltiseMember


@pytest.mark.skip(reason="Takes too long to run")
def test_populate_saltise_members():
    members = [
        {
            "name": "Elizabeth S. Charles",
            "picture": "Liz-Charles_thumb-220x220.jpg",
        },
        {
            "name": "Sameer Bhatnagar",
            "picture": "Sameer-Bhatnagar-e1447969841535-220x219.jpg",
        },
        {
            "name": "Jonathon Sumner",
            "picture": "JonathonSumner2019-06-18-at-4.37.54-PM-220x220.png",
        },
        {"name": "Laura Winer", "picture": "Laura-Winer_thumb-220x220.jpg"},
    ]
    call_command("populate_saltise_members")
    for member in members:
        member_ = SaltiseMember.objects.get(name=member["name"])
        assert member["picture"].split(".")[0] in member_.picture.name
