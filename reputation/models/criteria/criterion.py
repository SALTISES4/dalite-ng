from django.core.exceptions import ValidationError


def validate_list_floats_greater_0(val):
    for x in val:
        try:
            n = float(x)
        except ValueError:
            raise ValidationError(
                "The values must be comma separated floats greather or equal "
                "to 0."
            )
        if n < 0:
            raise ValidationError(
                "The values must be comma separated floats greather or equal "
                "to 0."
            )
