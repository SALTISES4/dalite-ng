from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from dalite.views.errors import response_400

from ..mixins import student_check
from ..models import Category, Discipline, Subject, Teacher, User


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@require_GET
def search_users(request):
    """Return list of usernames"""
    if request.is_ajax():
        users = (
            Teacher.objects.filter(
                user__username__icontains=request.GET.get("term")
            )
            .exclude(user=request.user)
            .values_list("user__username", "user__pk")
        )

        return JsonResponse(
            [{"label": u[0], "value": u[1]} for u in users], safe=False
        )
    else:
        return response_400(request, msg="")


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@require_GET
def search_categories(request):
    """Return list of categories"""
    if request.is_ajax():
        categories = Category.objects.filter(
            title__icontains=request.GET.get("term")
        ).values_list("title", "id")

        return JsonResponse(
            [{"label": c[0], "value": c[1]} for c in categories], safe=False
        )
    else:
        return response_400(request, msg="")


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@require_GET
def search_usernames(request):
    """Return list of usernames"""
    if request.is_ajax():
        users = User.objects.filter(
            groups__name__in=[settings.TEACHER_GROUP],
            username__icontains=request.GET.get("term"),
        ).values_list("username", "id")

        return JsonResponse(
            [{"label": c[0], "value": c[1]} for c in users], safe=False
        )
    else:
        return response_400(request, msg="")


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@require_GET
def search_subjects(request):
    """Return list of subjects"""
    if request.is_ajax():
        subjects = Subject.objects.filter(
            title__icontains=request.GET.get("term")
        ).values_list("title", "id")

        return JsonResponse(
            [{"label": c[0], "value": c[1]} for c in subjects], safe=False
        )
    else:
        return response_400(request, msg="")


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@require_GET
def search_disciplines(request):
    """Return list of disciplines"""
    if request.is_ajax():
        disciplines = Discipline.objects.filter(
            title__icontains=request.GET.get("term")
        ).values_list("title", "id")

        return JsonResponse(
            [{"label": c[0], "value": c[1]} for c in disciplines], safe=False
        )
    else:
        return response_400(request, msg="")
