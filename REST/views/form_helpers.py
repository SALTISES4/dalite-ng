from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_safe

from peerinst.models import Assignment
from peerinst.views.decorators import (
    ajax_login_required,
    ajax_user_passes_test,
)


@require_safe
@ajax_login_required
@ajax_user_passes_test(lambda u: hasattr(u, "teacher"))
def check_assignment_id_is_valid(request):
    id = request.GET.get("id")
    validators = Assignment._meta.get_field("identifier").validators
    if id:
        try:
            any(v(id) for v in validators)
        except ValidationError:
            return JsonResponse({"valid": False})

        if Assignment.objects.filter(identifier=id).exists():
            return JsonResponse({"valid": False})

        return JsonResponse({"valid": True})

    response = JsonResponse({"msg": "Missing query string parameter"})
    response.status_code = 400
    return response


@require_safe
@ajax_login_required
@ajax_user_passes_test(lambda u: hasattr(u, "teacher"))
def get_assignment_help_texts(request):
    help_texts = {}
    required_fields = [
        "intro_page",
        "conclusion_page",
        "description",
        "title",
        "identifier",
    ]
    for field in Assignment._meta.get_fields(include_parents=False):
        if hasattr(field, "help_text") and field.name in required_fields:
            help_texts[field.name] = field.help_text.strip()

    return JsonResponse(help_texts)
