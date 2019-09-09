from django.contrib.admin.widgets import AdminTextareaWidget

from dalite.models.custom_fields import AdminCommaSepFieldWidget, CommaSepField


def test_to_python():
    field = CommaSepField()

    val = None
    assert field.to_python(val) == []

    val = "a,b,c"
    assert field.to_python(val) == ["a", "b", "c"]

    val = ["a", "b", "c"]
    assert field.to_python(val) == val


def test_to_python__distinct():
    field = CommaSepField(distinct=True)

    val = ["a", "a", "b", "c"]
    assert field.to_python(val) == ["a", "b", "c"]


def test_from_db_value():
    field = CommaSepField()

    val = None
    assert field.from_db_value(val) == []

    val = "a,b,c"
    assert field.from_db_value(val) == ["a", "b", "c"]

    val = ["a", "b", "c"]
    assert field.from_db_value(val) == val


def test_from_db_value__distinct():
    field = CommaSepField(distinct=True)

    val = ["a", "a", "b", "c"]
    assert field.from_db_value(val) == ["a", "b", "c"]


def test_get_prep_value():
    field = CommaSepField()

    val = ["a", "b", "c"]
    assert field.get_prep_value(val) == "a,b,c"


def test_formfield():
    field = CommaSepField()

    assert isinstance(
        field.formfield(widget=AdminTextareaWidget).widget,
        AdminCommaSepFieldWidget,
    )


def test_format_value():
    widget = AdminCommaSepFieldWidget()

    val = u"['a', 'b', 'c']"
    assert widget.format_value(val) == "a, b, c"

    val = None
    assert widget.format_value(val) == ""
