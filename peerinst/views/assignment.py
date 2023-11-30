import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from dalite.views.errors import response_400
from peerinst.models import Assignment, Question

from .decorators import teacher_required


@login_required
@require_http_methods(["POST"])
@teacher_required
def update_assignment_question_list(req, teacher):
    post_data = json.loads(req.body)

    try:
        question_id = post_data["question_id"]
        assignment_identifier = post_data["assignment_identifier"]
    except KeyError:
        return response_400(req, msg=_("There are missing parameters."))

    try:
        assignment = Assignment.objects.get(identifier=assignment_identifier)
    except Assignment.DoesNotExist:
        return response_400(req, msg=_("Some parameters are wrong."))

    # Check object permissions (to be refactored using mixin)
    if req.user in assignment.owner.all() or req.user.is_staff:
        # Check for student answers
        if not assignment.is_editable:
            raise PermissionDenied
    else:
        raise PermissionDenied

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return response_400(req, msg=_("Some parameters are wrong."))

    if question in assignment.questions.all():
        assignment.questions.remove(question)
    else:
        assignment.questions.add(question)
    assignment.save()
    return HttpResponse("Success")
