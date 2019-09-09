from peerinst.models import MessageType


def test_message_types_exist():
    for type_ in (
        ("new_user", True),
        ("saltise_annoncement", False),
        ("dalite_annoncement", True),
    ):
        message_type = MessageType.objects.get(type=type_[0])
        assert message_type.removable is type_[1]
