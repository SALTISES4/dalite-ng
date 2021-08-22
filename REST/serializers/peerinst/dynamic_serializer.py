from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that controls
    which fields should be displayed
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        # Add filter based on querystring
        if "request" in self.context:
            requested_fields = self.context["request"].GET.getlist("field")
            if requested_fields:
                allowed = set(requested_fields)
                existing = set(self.fields)
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
