from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    ModelSerializer that allows dynamic filtering of fields via querystring.

    Attributes:
        fields: The fields to be included in the serialization.

    Examples:
        To include only specific fields in the serialization, pass the desired
        fields as a list in the `fields` argument:

        serializer = DynamicFieldsModelSerializer(fields=["field1", "field2"])

        This will ensure that only the specified fields are included in the
        serialized output.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        # Add filter based on querystring
        if "request" in self.context:
            if requested_fields := self.context["request"].GET.getlist(
                "field"
            ):
                allowed = set(requested_fields)
                existing = set(self.fields)
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
