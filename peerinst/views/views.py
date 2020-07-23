import json
import logging
import random
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import mail_admins, send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

# reports
from django.db.models import Count, Q
from django.db.models.expressions import Func
from django.forms import Textarea, inlineformset_factory

# blink
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.views.decorators.http import require_POST, require_safe
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView
from django_lti_tool_provider.models import LtiUserData
from django_lti_tool_provider.signals import Signals
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from dalite.views.errors import response_400, response_404

# tos
from tos.models import Consent, Tos

from .. import admin, forms, models, rationale_choice
from ..admin_views import get_question_rationale_aggregates
from ..mixins import (
    LoginRequiredMixin,
    NoStudentsMixin,
    ObjectPermissionMixin,
    TOSAcceptanceRequiredMixin,
    student_check,
    teacher_tos_accepted_check,
)
from ..models import AnswerChoice  # LtiEvent,
from ..models import (
    Answer,
    Assignment,
    BlinkAnswer,
    BlinkAssignment,
    BlinkAssignmentQuestion,
    BlinkQuestion,
    BlinkRound,
    Category,
    Collection,
    Discipline,
    NewUserRequest,
    Question,
    RationaleOnlyQuestion,
    ShownRationale,
    Student,
    StudentGroup,
    StudentGroupAssignment,
    StudentGroupCourse,
    Subject,
    Teacher,
    UserType,
    UserUrl,
)
from ..tasks import mail_admins_async
from ..util import (
    SessionStageData,
    get_object_or_none,
    get_student_activity_data,
    int_or_none,
    question_search_function,
    report_data_by_assignment,
    report_data_by_question,
    report_data_by_student,
    roundrobin,
)
from ..stopwords import fr, en

from course_flow.views import setup_link_to_group, setup_unlink_from_group

LOGGER = logging.getLogger(__name__)
LOGGER_teacher_activity = logging.getLogger("teacher_activity")


# Views related to Auth
@require_safe
def landing_page(request):

    disciplines = {}

    disciplines[str("All")] = {}
    disciplines[str("All")][str("questions")] = Question.objects.count()
    disciplines[str("All")][str("rationales")] = Answer.objects.count()
    disciplines[str("All")][str("students")] = Student.objects.count()
    disciplines[str("All")][str("teachers")] = Teacher.objects.count()

    for d in Discipline.objects.annotate(num_q=Count("question")).order_by(
        "-num_q"
    )[:3]:
        disciplines[str(d.title)] = {}
        disciplines[str(d.title)][str("questions")] = Question.objects.filter(
            discipline=d
        ).count()
        disciplines[str(d.title)][str("rationales")] = Answer.objects.filter(
            question__discipline=d
        ).count()

        question_list = d.question_set.values_list("id", flat=True)
        disciplines[str(d.title)][str("students")] = len(
            set(
                Answer.objects.filter(question_id__in=question_list)
                .exclude(user_token="")
                .values_list("user_token", flat=True)
            )
        )

        disciplines[str(d.title)]["teachers"] = d.teacher_set.count()

    disciplines_json = json.dumps(disciplines)

    # try again, with re-ordering
    disciplines_array = []

    d2 = {}
    d2[str("name")] = str("All")
    d2[str("questions")] = Question.objects.count()
    d2[str("rationales")] = Answer.objects.count()
    d2[str("students")] = Student.objects.count()
    d2[str("teachers")] = Teacher.objects.count()

    disciplines_array.append(d2)

    for d in Discipline.objects.annotate(num_q=Count("question")).order_by(
        "-num_q"
    )[:3]:
        d2 = {}
        d2[str("name")] = str(d.title)
        d2[str("questions")] = Question.objects.filter(discipline=d).count()
        d2[str("rationales")] = Answer.objects.filter(
            question__discipline=d
        ).count()

        question_list = d.question_set.values_list("id", flat=True)
        disciplines[str(d.title)][str("students")] = len(
            set(
                Answer.objects.filter(question_id__in=question_list)
                .exclude(user_token="")
                .values_list("user_token", flat=True)
            )
        )

        d2[str("teachers")] = d.teacher_set.count()

        disciplines_array.append(d2)

    return TemplateResponse(
        request,
        "registration/landing_page.html",
        context={"disciplines": disciplines_array, "json": disciplines_json},
    )


def sign_up(request):
    template = "registration/sign_up.html"
    html_email_template_name = "registration/sign_up_admin_email_html.html"
    context = {}

    if request.method == "POST":
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            # Set new users as inactive until verified by an administrator
            form.instance.is_active = False
            form.save()
            # Notify administrators

            #  print(settings.EMAIL_BACKEND)
            if not settings.EMAIL_BACKEND.startswith(
                "django.core.mail.backends"
            ):
                return HttpResponse(status=503)

            # TODO Adapt to different types of user
            NewUserRequest.objects.create(
                user=form.instance, type=UserType.objects.get(type="teacher")
            )
            UserUrl.objects.create(
                user=form.instance, url=form.cleaned_data["url"]
            )

            email_context = dict(
                user=form.cleaned_data["username"],
                date=timezone.now(),
                email=form.cleaned_data["email"],
                url=form.cleaned_data["url"],
                site_name="myDALITE",
            )
            mail_admins_async(
                "New user request",
                "Dear administrator,"
                "\n\nA new user {} was created on {}.".format(
                    form.cleaned_data["username"], timezone.now()
                )
                + "\n\nEmail: {}".format(form.cleaned_data["email"])
                + "\nVerification url: {}".format(form.cleaned_data["url"])
                + "\n\nAccess your administrator account to activate this "
                "new user."
                "\n\n{}://{}{}".format(
                    request.scheme,
                    request.get_host(),
                    reverse("saltise-admin:new-user-approval"),
                )
                + "\n\nCheers,"
                "\nThe myDalite Team",
                fail_silently=True,
                html_message=loader.render_to_string(
                    html_email_template_name,
                    context=email_context,
                    request=request,
                ),
            )

            return TemplateResponse(request, "registration/sign_up_done.html")
        else:
            context["form"] = form
    else:
        context["form"] = forms.SignUpForm()

    return render(request, template, context)


def admin_check(user):
    return user.is_superuser


def terms_teacher(request):
    tos, err = Tos.get("teacher")
    return TemplateResponse(
        request, "registration/terms.html", context={"tos": tos}
    )


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


@login_required
def welcome(request):
    if Teacher.objects.filter(user=request.user).exists():
        teacher = Teacher.objects.get(user=request.user)
        # Check if teacher group exists and ensure _this_ teacher belongs to it
        teacher_group = get_object_or_none(Group, name=settings.TEACHER_GROUP)
        if teacher_group:
            if teacher_group not in teacher.user.groups.all():
                teacher.user.groups.add(teacher_group)
        #  return HttpResponseRedirect(reverse("browse-database"))
        return HttpResponseRedirect(reverse("teacher-dashboard"))

    elif Student.objects.filter(student=request.user).exists():
        return HttpResponseRedirect(reverse("student-page"))

    elif request.user.is_staff:
        return HttpResponseRedirect(reverse("saltise-admin:index"))
    else:
        return logout_view(request)


def access_denied(request):
    raise PermissionDenied


def access_denied_and_logout(request):
    logout(request)
    raise PermissionDenied


@login_required
def browse_database(request):

    return TemplateResponse(
        request, "peerinst/browse_database.html", context={}
    )


class AssignmentListView(LoginRequiredMixin, NoStudentsMixin, ListView):
    """List of assignments used for debugging purposes."""

    model = models.Assignment


class AssignmentCopyView(LoginRequiredMixin, NoStudentsMixin, CreateView):
    """View to create an assignment from existing."""

    model = models.Assignment
    form_class = forms.AssignmentCreateForm

    def get_initial(self, *args, **kwargs):
        super(AssignmentCopyView, self).get_initial(*args, **kwargs)
        assignment = get_object_or_404(
            models.Assignment, pk=self.kwargs["assignment_id"]
        )
        initial = {"title": _("Copy of ") + assignment.title}
        return initial

    def get_object(self, queryset=None):
        # Remove link on object to pk to dump object permissions
        return None

    def get_context_data(self, **kwargs):
        context = super(AssignmentCopyView, self).get_context_data(**kwargs)
        teacher = get_object_or_404(models.Teacher, user=self.request.user)
        context["teacher"] = teacher
        return context

    # Custom save is needed to attach questions and user
    def form_valid(self, form):
        assignment = get_object_or_404(
            models.Assignment, pk=self.kwargs["assignment_id"]
        )
        form.instance.save()
        form.instance.questions = assignment.questions.all()
        form.instance.owner.add(self.request.user)
        teacher = get_object_or_404(models.Teacher, user=self.request.user)
        teacher.assignments.add(form.instance)
        teacher.save()
        return super(AssignmentCopyView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            "assignment-update", kwargs={"assignment_id": self.object.pk}
        )


class AssignmentEditView(LoginRequiredMixin, NoStudentsMixin, UpdateView):
    """View for editing assignment title and identifier."""

    model = Assignment
    template_name_suffix = "_edit"
    fields = ["title"]

    def get_object(self):
        return get_object_or_404(
            models.Assignment, pk=self.kwargs["assignment_id"]
        )

    def get_context_data(self, **kwargs):
        context = super(AssignmentEditView, self).get_context_data(**kwargs)
        teacher = get_object_or_404(models.Teacher, user=self.request.user)
        context["teacher"] = teacher
        return context

    def get_success_url(self):
        return reverse(
            "assignment-update", kwargs={"assignment_id": self.object.pk}
        )


class AssignmentUpdateView(LoginRequiredMixin, NoStudentsMixin, DetailView):
    """View for updating assignment."""

    model = Assignment

    def dispatch(self, *args, **kwargs):
        # Check object permissions (to be refactored using mixin)
        if (
            self.request.user in self.get_object().owner.all()
            or self.request.user.is_staff
        ):
            # Check for student answers
            if not self.get_object().editable:
                raise PermissionDenied
            else:
                return super(AssignmentUpdateView, self).dispatch(
                    *args, **kwargs
                )
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(AssignmentUpdateView, self).get_context_data(**kwargs)
        teacher = get_object_or_404(models.Teacher, user=self.request.user)
        context["teacher"] = teacher
        all_qs = (
            teacher.user.question_set.all() | teacher.user.collaborators.all()
        )
        context["all_questions"] = all_qs.distinct()
        return context

    def get_object(self):
        return get_object_or_404(
            models.Assignment, pk=self.kwargs["assignment_id"]
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = forms.AddRemoveQuestionForm(request.POST)
        if form.is_valid():
            question = form.cleaned_data["q"]
            if question not in self.object.questions.all():
                self.object.questions.add(question)
            else:
                self.object.questions.remove(question)
            self.object.save()
            return HttpResponseRedirect(
                reverse(
                    "assignment-update",
                    kwargs={"assignment_id": self.object.pk},
                )
            )
        else:
            return response_400(request)


class QuestionListView(LoginRequiredMixin, NoStudentsMixin, ListView):
    """List of questions used for debugging purposes."""

    model = models.Assignment
    template_name = "peerinst/question/list.html"

    def get_queryset(self):
        self.assignment = get_object_or_404(
            models.Assignment, pk=self.kwargs["assignment_id"]
        )
        return self.assignment.questions.all()

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)
        context.update(assignment=self.assignment)
        return context


# Views related to Question
class QuestionCreateView(
    LoginRequiredMixin,
    NoStudentsMixin,
    ObjectPermissionMixin,
    TOSAcceptanceRequiredMixin,
    CreateView,
):
    """View to create a new question outside of admin."""

    object_permission_required = "peerinst.add_question"
    model = models.Question
    fields = [
        "title",
        "text",
        "type",
        "image",
        "image_alt_text",
        "video_url",
        "answer_style",
        "category",
        "discipline",
        "collaborators",
        "fake_attributions",
        "sequential_review",
        "rationale_selection_algorithm",
        "grading_scheme",
    ]

    template_name = "peerinst/question/form.html"

    # Custom save is needed to attach user to question
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(QuestionCreateView, self).form_valid(form)

    def get_success_url(self):
        if self.object.type == "RO":
            return reverse(
                "sample-answer-form", kwargs={"question_id": self.object.pk}
            )
        else:
            return reverse(
                "answer-choice-form", kwargs={"question_id": self.object.pk}
            )


class QuestionCloneView(QuestionCreateView):
    """View to create a question from existing."""

    template_name = "peerinst/question/form.html"

    def get_initial(self, *args, **kwargs):
        super(QuestionCloneView, self).get_initial(*args, **kwargs)
        question = get_object_or_404(models.Question, pk=self.kwargs["pk"])
        initial = {
            "text": question.text,
            "type": question.type,
            "image": question.image,
            "image_alt_text": question.image_alt_text,
            "video_url": question.video_url,
            "answer_style": question.answer_style,
            "category": question.category.all(),
            "discipline": question.discipline,
            "fake_attributions": question.fake_attributions,
            "sequential_review": question.sequential_review,
            "rationale_selection_algorithm": question.rationale_selection_algorithm,  # noqa
            "grading_scheme": question.grading_scheme,
        }
        return initial

    def get_object(self, queryset=None):
        # Remove link on object to pk to dump object permissions
        return None

    # Custom save is needed to attach parent question to clone
    def form_valid(self, form):
        form.instance.parent = get_object_or_404(
            models.Question, pk=self.kwargs["pk"]
        )
        return super(QuestionCloneView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(QuestionCloneView, self).get_context_data(**kwargs)
        context.update(
            parent=get_object_or_404(models.Question, pk=self.kwargs["pk"])
        )
        return context


class QuestionUpdateView(
    LoginRequiredMixin,
    NoStudentsMixin,
    ObjectPermissionMixin,
    TOSAcceptanceRequiredMixin,
    UpdateView,
):
    """View to edit a new question outside of admin."""

    object_permission_required = "peerinst.change_question"
    model = models.Question
    fields = [
        "title",
        "text",
        "type",
        "image",
        "image_alt_text",
        "video_url",
        "answer_style",
        "category",
        "discipline",
        "collaborators",
        "fake_attributions",
        "sequential_review",
        "rationale_selection_algorithm",
        "grading_scheme",
    ]

    template_name = "peerinst/question/form.html"

    def get_form(self, form_class=None):
        # Check if student answers exist
        if self.object.answer_set.exclude(user_token__exact="").count() > 0:
            return None
        else:
            return super(QuestionUpdateView, self).get_form(form_class)

    def post(self, request, *args, **kwargs):
        # Check if student answers exist
        if (
            self.get_object().answer_set.exclude(user_token__exact="").count()
            > 0
        ):
            raise PermissionDenied
        else:
            return super(QuestionUpdateView, self).post(
                request, *args, **kwargs
            )

    def form_valid(self, form):
        # Only owner can update collaborators
        if not self.object.user == self.request.user:
            form.cleaned_data[
                "collaborators"
            ] = self.object.collaborators.all()
        return super(QuestionUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(QuestionUpdateView, self).get_context_data(**kwargs)
        context.update(parent=self.object.parent)
        return context

    def get_success_url(self):
        if self.object.type == "RO":
            return reverse(
                "sample-answer-form", kwargs={"question_id": self.object.pk}
            )
        else:
            return reverse(
                "answer-choice-form", kwargs={"question_id": self.object.pk}
            )


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@require_POST
def question_delete(request):
    """Hide questions that a teacher deletes."""
    if request.is_ajax():
        # Ajax only
        question = get_object_or_404(Question, pk=request.POST.get("pk"))
        teacher = get_object_or_404(Teacher, user=request.user)
        if question not in teacher.deleted_questions.all():
            teacher.deleted_questions.add(question)
            return JsonResponse({"action": "delete"})
        else:
            teacher.deleted_questions.remove(question)
            return JsonResponse({"action": "restore"})
    else:
        return response_400(request)


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@user_passes_test(teacher_tos_accepted_check, login_url="/tos/required/")
def answer_choice_form(request, question_id):
    AnswerChoiceFormSet = inlineformset_factory(
        Question,
        AnswerChoice,
        form=forms.AnswerChoiceForm,
        fields=("text", "correct"),
        widgets={"text": Textarea(attrs={"rows": 3})},
        formset=admin.AnswerChoiceInlineFormSet,
        max_num=5,
        extra=5,
    )
    question = get_object_or_404(models.Question, pk=question_id)
    request.session["question_id"] = question_id

    # Check permissions
    if request.user.has_perm("peerinst.change_question", question):

        # Check if student answers exist
        if question.answer_set.exclude(user_token__exact="").count() > 0:
            return TemplateResponse(
                request,
                "peerinst/question/answer_choice_form.html",
                context={"question": question},
            )

        if request.method == "POST":
            # Populate form; resend if invalid
            formset = AnswerChoiceFormSet(request.POST, instance=question)
            if formset.is_valid():
                instances = formset.save()
                return HttpResponseRedirect(
                    reverse(
                        "research-fix-expert-rationale",
                        kwargs={"question_id": question.pk},
                    )
                )
        else:
            if question.answerchoice_set.count() == 0 and question.parent:
                formset = AnswerChoiceFormSet(
                    instance=question,
                    initial=[
                        a.__dict__
                        for a in question.parent.answerchoice_set.all()
                    ],
                )
            else:
                formset = AnswerChoiceFormSet(instance=question)

        return TemplateResponse(
            request,
            "peerinst/question/answer_choice_form.html",
            context={"question": question, "formset": formset},
        )
    else:
        raise PermissionDenied


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@user_passes_test(teacher_tos_accepted_check, login_url="/tos/required/")
def sample_answer_form_done(request, question_id):
    question = get_object_or_404(models.Question, pk=question_id)

    if request.method == "POST":
        try:
            teacher = Teacher.objects.get(user=request.user)
            form = forms.AssignmentMultiselectForm(
                request.user, question, request.POST
            )
            if form.is_valid():
                assignments = form.cleaned_data["assignments"].all()
                for a in assignments:
                    if teacher.user in a.owner.all():
                        # Check for student answers
                        if (
                            a.answer_set.exclude(user_token__exact="").count()
                            == 0
                            and question not in a.questions.all()
                        ):
                            a.questions.add(question)
                    else:
                        raise PermissionDenied

            return HttpResponseRedirect(
                reverse("teacher", kwargs={"pk": teacher.pk})
            )
        except Exception:
            return response_400(request)
    else:
        return response_400(request)


class DisciplineCreateView(
    LoginRequiredMixin, NoStudentsMixin, TOSAcceptanceRequiredMixin, CreateView
):
    """View to create a new discipline outside of admin."""

    model = Discipline
    fields = ["title"]

    def get_success_url(self):
        if self.request.GET.get("multiselect", False):
            return reverse("disciplines-form", kwargs={"pk": self.object.pk})
        else:
            return reverse("discipline-form", kwargs={"pk": self.object.pk})


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@user_passes_test(teacher_tos_accepted_check, login_url="/tos/required/")
def discipline_select_form(request, pk=None):
    """
    An AJAX view that simply renders the DisciplineSelectForm. Preselects
    instance with pk, if given.
    """
    if pk:
        form = forms.DisciplineSelectForm(
            initial={"discipline": Discipline.objects.get(pk=pk)}
        )
    else:
        form = forms.DisciplineSelectForm()

    return TemplateResponse(
        request, "peerinst/discipline_select_form.html", context={"form": form}
    )


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def disciplines_select_form(request, pk=None):
    """
    AJAX view simply renders the DisciplinesSelectForm. Preselects instance
    with teachers current set.
    """

    disciplines = request.user.teacher.disciplines.values_list("pk", flat=True)

    if pk:
        disciplines = Discipline.objects.filter(
            Q(pk=pk) | Q(pk__in=disciplines)
        )

    form = forms.DisciplinesSelectForm(initial={"disciplines": disciplines})

    return TemplateResponse(
        request,
        "peerinst/disciplines_select_form.html",
        context={"form": form},
    )


class CategoryCreateView(
    LoginRequiredMixin, NoStudentsMixin, TOSAcceptanceRequiredMixin, CreateView
):
    """ View to create a new category outside of admin. """

    model = Category
    fields = ["title"]

    def get_success_url(self):
        return reverse("category-form", kwargs={"pk": self.object.pk})


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
@user_passes_test(teacher_tos_accepted_check, login_url="/tos/required/")
def category_select_form(request, pk=None):
    """
    AJAX view simply renders the CategorySelectForm. Preselects instance with
    pk, if given.
    """
    if pk:
        form = forms.CategorySelectForm(
            initial={"category": [Category.objects.get(pk=pk)]}
        )
    else:
        form = forms.CategorySelectForm()

    return TemplateResponse(
        request, "peerinst/category_select_form.html", context={"form": form}
    )


class QuestionMixin(object):
    def get_context_data(self, **kwargs):
        context = super(QuestionMixin, self).get_context_data(**kwargs)
        context.update(
            assignment=self.assignment,
            question=self.question,
            answer_choices=self.answer_choices,
            correct=self.question.answerchoice_set.filter(correct=True),
            experts=self.question.answer_set.filter(expert=True),
        )

        # Pass hints so that template knows context
        if self.request.session.get("LTI"):
            context.update(lti=True)
        else:
            context.update(lti=False)
            hash = self.request.session.get("assignment")
            if hash is not None:
                group_assignment = StudentGroupAssignment.get(hash)
                context.update(group_assignment=group_assignment)
            context.update(
                assignment_first=self.request.session.get("assignment_first")
            )
            context.update(
                assignment_last=self.request.session.get("assignment_last")
            )
            context.update(
                assignment_expired=self.request.session.get(
                    "assignment_expired"
                )
            )
            context.update(quality=self.request.session.get("quality"))

        return context

    def send_grade(self):
        if not self.lti_data:
            # We are running outside of an LTI context, so we don't need to
            # send a grade.
            return
        if not self.lti_data.edx_lti_parameters.get("lis_outcome_service_url"):
            # edX didn't provide a callback URL for grading, so this is an
            # unscored problem.
            return

        Signals.Grade.updated.send(
            __name__,
            user=self.request.user,
            custom_key=self.custom_key,
            grade=self.answer.grade,
        )


class QuestionReload(Exception):
    """
    Raised to cause a reload of the page, usually to start over in case of an
    error.
    """


class QuestionFormView(QuestionMixin, FormView):
    """Base class for the form views in the student UI."""

    template_name = "peerinst/question/form.html"

    def dispatch(self, *args, **kwargs):
        # Check for any TOS
        if Consent.get(self.request.user.username, "student") is None:
            return HttpResponseRedirect(
                reverse("tos:tos_consent", kwargs={"role": "student"})
                + "?next="
                + self.request.path
            )
        else:
            latest_student_consent = (
                Consent.objects.filter(
                    user__username=self.request.user.username,
                    tos__role="student",
                )
                .order_by("-datetime")
                .first()
            )
            # Check if TOS is current
            if not latest_student_consent.tos.current:
                return HttpResponseRedirect(
                    reverse("tos:tos_consent", kwargs={"role": "student"})
                    + "?next="
                    + self.request.path
                )
            else:
                return super(QuestionFormView, self).dispatch(*args, **kwargs)

    def emit_event(self, name, **data):
        """
        Log an event in a JSON format similar to the edx-platform tracking
        logs.
        """
        if self.lti_data:
            # Extract information from LTI parameters.
            course_id = self.lti_data.edx_lti_parameters.get("context_id")

            try:
                edx_org = CourseKey.from_string(course_id).org
            except InvalidKeyError:
                # The course_id is not from edX. Don't place the org in the
                # logs.
                edx_org = None

            grade_handler_re = re.compile(
                "https?://[^/]+/courses/{}".format(re.escape(course_id))
                + "/xblock/(?P<usage_key>[^/]+)/"
            )
            usage_key = None
            outcome_service_url = self.lti_data.edx_lti_parameters.get(
                "lis_outcome_service_url"
            )
            if outcome_service_url:
                usage_key = grade_handler_re.match(outcome_service_url)
                if usage_key:
                    usage_key = usage_key.group("usage_key")
                # Grading is enabled, so include information about max grade in
                # event data
                data["max_grade"] = 1.0
            else:
                # Grading is not enabled, so remove information about grade
                # from event data
                if "grade" in data:
                    del data["grade"]
        else:
            edx_org = None
            course_id = "standalone"
            usage_key = None

        # Add common fields to event data
        data.update(
            assignment_id=self.assignment.pk,
            assignment_title=self.assignment.title,
            problem=usage_key,
            question_id=self.question.pk,
            question_text=self.question.text,
        )

        # Build event dictionary
        META = self.request.META
        event = dict(
            accept_language=META.get("HTTP_ACCEPT_LANGUAGE"),
            agent=META.get("HTTP_USER_AGENT"),
            context=dict(
                course_id=course_id,
                module=dict(usage_key=usage_key),
                username=self.user_token,
            ),
            course_id=course_id,
            event=data,
            event_source="server",
            event_type=name,
            host=META.get("SERVER_NAME"),
            ip=META.get("HTTP_X_REAL_IP", META.get("REMOTE_ADDR")),
            referer=META.get("HTTP_REFERER"),
            time=datetime.now().isoformat(),
            username=self.user_token,
        )

        if edx_org is not None:
            event["context"]["org_id"] = edx_org

        # Write JSON to log file
        LOGGER.info(json.dumps(event))
        # lti_event = LtiEvent(
        #     event_type=name,
        #     event_log=json.dumps(event),
        #     username=self.user_token,
        #     assignment_id=self.assignment.identifier,
        #     question_id=self.question.pk,
        # )
        # lti_event.save()

        if self.lti_data:
            course_title = self.lti_data.edx_lti_parameters.get(
                "context_title"
            )

            try:
                group = StudentGroup.objects.get(name=course_id)
            except StudentGroup.DoesNotExist:
                if course_title:
                    group = StudentGroup(name=course_id, title=course_title)
                else:
                    group = StudentGroup(name=course_id)
                group.save()

            # If teacher_id specified, add teacher to group
            teacher_hash = self.lti_data.edx_lti_parameters.get(
                "custom_teacher_id"
            )
            if teacher_hash is not None:
                teacher = Teacher.get(teacher_hash)
                if teacher not in group.teacher.all():
                    group.teacher.add(teacher)
                    teacher.current_groups.add(group)
                    teacher.save()

            # If this user is a student, add group to student
            if hasattr(self.request.user, "student"):
                self.request.user.student.groups.add(group)

    def submission_error(self):
        messages.error(
            self.request,
            format_html(
                '<h3 class="messages-title">{}</h3>{}',
                _("There was a problem with your submission"),
                _("Check the form below."),
            ),
        )

    # def form_invalid(self, form):
    #     self.submission_error()
    #     return super(QuestionFormView, self).form_invalid(form)

    def get_success_url(self):
        # We always redirect to the same HTTP endpoint.  The actual view is
        # selected based on the session state.
        return self.request.path

    def start_over(self, msg=None):
        """
        Start over with the current question. This redirect is used when
        inconsistent data is encountered and shouldn't be called under normal
        circumstances.
        """
        if msg is not None:
            messages.error(self.request, msg)
        raise QuestionReload()


class QuestionStartView(QuestionFormView):
    """Render a question with or without answer choices depending on type.

    The user can choose one answer and enter a rationale.
    """

    template_name = "peerinst/question/start.html"

    def get_form_class(self):
        return self.question.get_start_form_class()

    def get_form_kwargs(self):
        kwargs = super(QuestionStartView, self).get_form_kwargs()
        kwargs.update(answer_choices=self.answer_choices)
        if self.request.method == "GET":
            # Log when the page is first shown, mainly for the timestamp.
            self.emit_event("problem_show")
        return kwargs

    def form_valid(self, form):
        self.question.start_form_valid(self, form)

        return super(QuestionStartView, self).form_valid(form)


class QuestionReviewBaseView(QuestionFormView):
    """Common base class for sequential and non-sequential review types."""

    def determine_rationale_choices(self):
        if not hasattr(self, "choose_rationales"):
            self.choose_rationales = rationale_choice.algorithms[
                self.question.rationale_selection_algorithm
            ]
        self.rationale_choices = self.stage_data.get("rationale_choices")
        if self.rationale_choices is not None:
            # The rationales we stored in the session have already been
            # HTML-escaped – mark them as safe to avoid double-escaping
            self.mark_rationales_safe(escape_html=False)
            return
        # Make the choice of rationales deterministic, so rationales won't
        # change when reloading the page after clearing the session.
        rng = random.Random(
            (self.user_token, self.assignment.pk, self.question.pk)
        )
        try:
            self.rationale_choices = self.choose_rationales(
                rng, self.first_answer_choice, self.rationale, self.question
            )
        except rationale_choice.RationaleSelectionError as e:
            self.start_over(str(e))
        if self.question.fake_attributions:
            self.add_fake_attributions(rng)
        else:
            self.mark_rationales_safe(escape_html=True)
        self.stage_data.update(rationale_choices=self.rationale_choices)

    def mark_rationales_safe(self, escape_html):
        if escape_html:
            processor = escape
        else:
            processor = mark_safe
        for choice, label, rationales in self.rationale_choices:
            rationales[:] = [(id, processor(text)) for id, text in rationales]

    def add_fake_attributions(self, rng):
        usernames = models.FakeUsername.objects.values_list("name", flat=True)
        countries = models.FakeCountry.objects.values_list("name", flat=True)
        if not usernames or not countries:
            # No usernames or no countries were supplied, so we silently
            # refrain from adding fake attributions.  We need to ensure,
            # though, that the rationales get properly escaped.
            self.mark_rationales_safe(escape_html=True)
            return
        fake_attributions = {}
        for choice, label, rationales in self.rationale_choices:
            attributed_rationales = []
            for id, text in rationales:
                if id is None:
                    # This is the "I stick with my own rationale" option.
                    # Don't add a fake attribution, it might blow our cover.
                    attributed_rationales.append((id, text))
                    continue
                attribution = rng.choice(usernames), rng.choice(countries)
                fake_attributions[id] = attribution
                formatted_rationale = format_html(
                    "<q>{}</q> ({}, {})", text, *attribution
                )
                attributed_rationales.append((id, formatted_rationale))
            rationales[:] = attributed_rationales
        self.stage_data.update(fake_attributions=fake_attributions)

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewBaseView, self).get_form_kwargs()
        self.first_answer_choice = self.stage_data.get("first_answer_choice")
        self.rationale = self.stage_data.get("rationale")
        self.datetime_start = datetime.strptime(
            self.stage_data.get("datetime_start"), "%Y-%m-%d %H:%M:%S.%f"
        ).replace(tzinfo=pytz.UTC)
        self.datetime_first = datetime.strptime(
            self.stage_data.get("datetime_first"), "%Y-%m-%d %H:%M:%S.%f"
        ).replace(tzinfo=pytz.UTC)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionReviewBaseView, self).get_context_data(
            **kwargs
        )
        context.update(
            first_choice_label=self.question.get_choice_label(
                self.first_answer_choice
            ),
            rationale=self.rationale,
            sequential_review=self.stage_data.get("completed_stage")
            == "sequential-review",
        )
        return context


class QuestionSequentialReviewView(QuestionReviewBaseView):

    template_name = "peerinst/question/sequential_review.html"
    form_class = forms.SequentialReviewForm

    def select_next_rationale(self):
        rationale_sequence = self.stage_data.get("rationale_sequence")
        if rationale_sequence:
            # We already have selected the rationales – just take the next one.
            self.current_rationale = rationale_sequence[
                self.stage_data.get("rationale_index")
            ]
            self.current_rationale[2] = mark_safe(self.current_rationale[2])
            return
        self.choose_rationales = rationale_choice.simple_sequential
        self.determine_rationale_choices()
        # Select alternating rationales from the lists of rationales for the
        # different answer choices.  Skip the "I stick with my own rationale"
        # option marked by id == None.
        rationale_sequence = list(
            roundrobin(
                [
                    (id, label, rationale)
                    for id, rationale in rationales
                    if id is not None
                ]
                for choice, label, rationales in self.rationale_choices
            )
        )
        self.current_rationale = rationale_sequence[0]
        self.stage_data.update(
            rationale_sequence=rationale_sequence,
            rationale_votes={},
            rationale_index=0,
        )

    def get_context_data(self, **kwargs):
        context = super(QuestionSequentialReviewView, self).get_context_data(
            **kwargs
        )
        self.select_next_rationale()
        context.update(current_rationale=self.current_rationale)
        return context

    def form_valid(self, form):
        rationale_sequence = self.stage_data.get("rationale_sequence")
        rationale_votes = self.stage_data.get("rationale_votes")
        rationale_index = self.stage_data.get("rationale_index")
        current_rationale = rationale_sequence[rationale_index]
        rationale_votes[current_rationale[0]] = form.cleaned_data["vote"]
        rationale_index += 1
        self.stage_data.update(
            rationale_index=rationale_index, rationale_votes=rationale_votes
        )
        if rationale_index == len(rationale_sequence):
            # We've shown all rationales – mark the stage as finished.
            self.stage_data.update(completed_stage="sequential-review")
        return super(QuestionSequentialReviewView, self).form_valid(form)


class QuestionReviewView(QuestionReviewBaseView):
    """
    The standard version of the review, showing all alternative rationales
    simultaneously.
    """

    template_name = "peerinst/question/review.html"
    form_class = forms.ReviewAnswerForm

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewView, self).get_form_kwargs()
        self.determine_rationale_choices()
        kwargs.update(rationale_choices=self.rationale_choices)
        return kwargs

    def form_valid(self, form):
        self.second_answer_choice = int(
            form.cleaned_data["second_answer_choice"]
        )
        self.chosen_rationale_id = int_or_none(
            form.cleaned_data["chosen_rationale_id"]
        )
        self.save_answer()
        self.emit_check_events()
        self.save_votes()
        self.stage_data.clear()
        self.send_grade()
        self.save_shown_rationales(form.shown_rationales)
        return super(QuestionReviewView, self).form_valid(form)

    def emit_check_events(self):
        grade = self.answer.grade
        event_data = dict(
            second_answer_choice=self.second_answer_choice,
            switch=self.first_answer_choice != self.second_answer_choice,
            rationale_algorithm=dict(
                name=self.question.rationale_selection_algorithm,
                version=self.choose_rationales.version,
                description=str(self.choose_rationales.description),
            ),
            rationales=[
                {"id": id, "text": rationale}
                for choice, label, rationales in self.rationale_choices
                for id, rationale in rationales
                if id is not None
            ],
            chosen_rationale_id=self.chosen_rationale_id,
            success="correct" if grade == 1.0 else "incorrect",
            grade=grade,
        )
        self.emit_event("problem_check", **event_data)
        self.emit_event("save_problem_success", **event_data)

    def save_answer(self):
        """
        Validate and save the answer defined by the arguments to the database.
        """
        if self.chosen_rationale_id is not None:
            try:
                chosen_rationale = models.Answer.objects.get(
                    id=self.chosen_rationale_id
                )
            except models.Answer.DoesNotExist:
                # Raises exception.
                self.start_over(
                    _(
                        "The rationale you chose does not exist anymore. This "
                        "should not happen.  Please start over with the "
                        "question."
                    )
                )
            if (
                chosen_rationale.first_answer_choice
                != self.second_answer_choice
            ):
                self.start_over(
                    _(
                        "The rationale you chose does not match your second "
                        "answer choice.  This should not happen.  Please "
                        "start over with the question."
                    )
                )
        else:
            # We stuck with our own rationale.
            chosen_rationale = None
        if self.stage_data.get("student_group_assignment_pk", None) is None:
            self.answer = models.Answer(
                question=self.question,
                assignment=self.assignment,
                first_answer_choice=self.first_answer_choice,
                rationale=self.rationale,
                second_answer_choice=self.second_answer_choice,
                chosen_rationale=chosen_rationale,
                user_token=self.user_token,
                datetime_start=self.datetime_start,
                datetime_first=self.datetime_first,
                datetime_second=datetime.now(pytz.utc),
            )
        else:
            self.answer = models.Answer(
                question=self.question,
                assignment=self.assignment,
                first_answer_choice=self.first_answer_choice,
                rationale=self.rationale,
                second_answer_choice=self.second_answer_choice,
                chosen_rationale=chosen_rationale,
                user_token=self.user_token,
                datetime_start=self.datetime_start,
                datetime_first=self.datetime_first,
                datetime_second=datetime.now(pytz.utc),
                student_group_assignment=models.StudentGroupAssignment.objects.filter(
                    pk=self.stage_data.get("student_group_assignment_pk")
                ).first(),
            )

        self.answer.save()
        if chosen_rationale is not None:
            self.record_fake_attribution_vote(
                chosen_rationale, models.AnswerVote.FINAL_CHOICE
            )

    def save_votes(self):
        rationale_votes = self.stage_data.get("rationale_votes")
        if rationale_votes is None:
            return
        for rationale_id, vote in rationale_votes.items():
            try:
                rationale = models.Answer.objects.get(id=rationale_id)
            except models.Answer.DoesNotExist:
                # This corner case can only happen if an answer was deleted
                # while the student was answering the question.  Simply ignore
                # these votes.
                continue
            if vote == "up":
                rationale.upvotes += 1
                self.record_fake_attribution_vote(
                    rationale, models.AnswerVote.UPVOTE
                )
            elif vote == "down":
                rationale.downvotes += 1
                self.record_fake_attribution_vote(
                    rationale, models.AnswerVote.DOWNVOTE
                )
            rationale.save()

    def record_fake_attribution_vote(self, answer, vote_type):
        fake_attributions = self.stage_data.get("fake_attributions")
        if fake_attributions is None:
            return
        fake_username, fake_country = fake_attributions[str(answer.id)]
        models.AnswerVote(
            answer=answer,
            assignment=self.assignment,
            user_token=self.user_token,
            fake_username=fake_username,
            fake_country=fake_country,
            vote_type=vote_type,
        ).save()

    def save_shown_rationales(self, shown_rationale_pks=None):
        """
        Saves in the databse which rationales were shown to the student. These
        are linked to the answer.
        Stick to my rationale is no longer saved as ShownRationale with an empty shown_answer
        """
        rationale_ids = [
            rationale[0]
            for _, _, rationales in self.rationale_choices
            for rationale in rationales
        ]
        shown_answers = (
            list(Answer.objects.filter(id__in=rationale_ids))
            if shown_rationale_pks is None
            else list(Answer.objects.filter(id__in=shown_rationale_pks))
        )
        if shown_rationale_pks is None and None in rationale_ids:
            shown_answers += [None]
        for answer in shown_answers:
            ShownRationale.objects.create(
                shown_for_answer=self.answer, shown_answer=answer
            )


class QuestionSummaryView(QuestionMixin, TemplateView):
    """
    Show a summary of answers to the student and submit the data to the
    database.
    """

    template_name = "peerinst/question/summary.html"

    def get_context_data(self, **kwargs):
        context = super(QuestionSummaryView, self).get_context_data(**kwargs)
        context.update(
            first_choice_label=self.answer.first_answer_choice_label(),
            second_choice_label=self.answer.second_answer_choice_label(),
            rationale=self.answer.rationale,
            chosen_rationale=self.answer.chosen_rationale,
        )
        self.send_grade()
        return context

    # If we get here via POST, it is likely from submitting an answer to a
    # question that has already been answered.  Simply redirect here as GET.
    def post(self, request, *args, **kwargs):
        return redirect(request.path)


class RationaleOnlyQuestionSummaryView(QuestionMixin, TemplateView):
    """
    Show a summary of answers to the student and submit the data to the
    database.
    """

    template_name = "peerinst/question/summary.html"

    def get_context_data(self, **kwargs):
        context = super(
            RationaleOnlyQuestionSummaryView, self
        ).get_context_data(**kwargs)
        context.update(rationale=self.answer.rationale)
        self.send_grade()
        return context

    # If we get here via POST, it is likely from submitting an answer to a
    # question that has already been answered.  Simply redirect here as GET.
    def post(self, request, *args, **kwargs):
        return redirect(request.path)


class AnswerSummaryChartView(View):
    """
    This view draws a chart showing analytics about the answers that students
    chose for a question, and the rationales that they selected to back up
    those answers.
    """

    def __init__(self, *args, **kwargs):
        """Save the initialization arguments for later use."""
        self.kwargs = kwargs
        super(AnswerSummaryChartView, self).__init__(*args, **kwargs)

    def get(self, request):
        """
        This method handles creation of a piece of context that can be used to
        draw the chart mentioned in the class docstring.
        """
        # Get the relevant assignment/question pairing
        question = self.kwargs.get("question")
        assignment = self.kwargs.get("assignment")
        # There are three columns that every chart will have - prefill them
        # here
        static_columns = [
            ("label", "Choice"),
            ("before", "Before"),
            ("after", "After"),
        ]
        # Other columns will be dynamically present, depending on which choices
        # were available on a given question.
        to_columns = [
            (
                "to_{}".format(question.get_choice_label(i)),
                "To {}".format(question.get_choice_label(i)),
            )
            for i in range(1, question.answerchoice_set.count() + 1)
        ]
        # Initialize a list of answers that we can add details to
        answers = []
        for i, answer in enumerate(question.answerchoice_set.all(), start=1):
            # Get the label for the row, and the counts for how many students
            # chose this answer the first time, and the second time.
            answer_row = {
                "label": "Answer {}: {}".format(
                    question.get_choice_label(i), answer.text
                ),
                "before": models.Answer.objects.filter(
                    question=question,
                    first_answer_choice=i,
                    assignment=assignment,
                ).count(),
                "after": models.Answer.objects.filter(
                    question=question,
                    second_answer_choice=i,
                    assignment=assignment,
                ).count(),
            }
            for j, column in enumerate(to_columns, start=1):
                # For every other answer, determine the count of students who
                # chose this answer the first time, but the other answer the
                # second time.
                answer_row[column[0]] = models.Answer.objects.filter(
                    question=question,
                    first_answer_choice=i,
                    second_answer_choice=j,
                    assignment=assignment,
                ).count()
            # Get the top five rationales for this answer to display underneath
            # the chart
            _, rationales = get_question_rationale_aggregates(
                assignment,
                question,
                5,
                choice_id=i,
                include_own_rationales=True,
            )
            answer_row["rationales"] = rationales["chosen"]
            # Save everything about this answer into the list of table rows
            answers.append(answer_row)
        # Build a list of all the columns that will be used in this chart
        columns = [
            {"name": name, "label": label}
            for name, label in static_columns + to_columns
        ]
        # Build a two-dimensional list with a value for each cell in the chart
        answer_rows = [
            [row[column["name"]] for column in columns] for row in answers
        ]
        # Transform the rationales we got from the other function into a format
        # we can easily draw in the page using a template
        answer_rationales = [
            {
                "label": each["label"],
                "rationales": [
                    {
                        "text": rationale["rationale"].rationale,
                        "count": rationale["count"],
                    }
                    for rationale in each["rationales"]
                    if rationale["rationale"] is not None
                ],
            }
            for each in answers
        ]
        # Render the template using the relevant variables and return it as an
        # HTTP response.
        return TemplateResponse(
            request,
            "peerinst/question/answers_summary.html",
            context={
                "question": question,
                "columns": columns,
                "answer_rows": answer_rows,
                "answer_rationales": answer_rationales,
            },
        )


def redirect_to_login_or_show_cookie_help(request):
    """
    Redirect to login page outside of an iframe, show help on enabling cookies
    inside an iframe. We consider the request to come from within an iframe if
    the HTTP Referer header is set. This isn't entirely accurate, but should
    be good enough.
    """
    if request.META.get("HTTP_REFERER"):
        # We probably got here from within the LMS, and the user has
        # third-party cookies disabled, so we show help on enabling cookies for
        # this site.
        return render(
            request, "peerinst/cookie_help.html", dict(host=request.get_host())
        )
    return redirect_to_login(request.get_full_path())


def question(request, assignment_id, question_id):
    """
    Load common question data and dispatch to the right question stage. This
    dispatcher loads the session state and relevant database objects. Based on
    the available data, it delegates to the correct view class.
    """
    if not request.user.is_authenticated:
        return redirect_to_login_or_show_cookie_help(request)

    # Collect common objects required for the view
    assignment = get_object_or_404(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)

    # Reload question through proxy based on type, if needed
    if question.type == "RO":
        question = get_object_or_404(RationaleOnlyQuestion, pk=question_id)

    custom_key = str(assignment.pk) + ":" + str(question.pk)
    stage_data = SessionStageData(request.session, custom_key)
    user_token = request.user.username

    if request.GET.get("student_group_assignment_pk", None) is not None:
        student_group_assignment = StudentGroupAssignment.objects.get(
            pk=int(request.GET.get("student_group_assignment_pk"))
        )
        latest_answer = models.Answer.objects.filter(
            assignment=assignment,
            question=question,
            user_token=user_token,
            student_group_assignment=student_group_assignment,
        ).last()
    else:
        latest_answer = models.Answer.objects.filter(
            assignment=assignment, question=question, user_token=user_token,
        ).last()

    view_data = dict(
        request=request,
        assignment=assignment,
        question=question,
        user_token=user_token,
        answer_choices=question.get_choices(),
        custom_key=custom_key,
        stage_data=stage_data,
        lti_data=get_object_or_none(
            LtiUserData, user=request.user, custom_key=custom_key
        ),
        answer=latest_answer,
    )

    # Determine stage and view class
    if request.GET.get("show_results_view") == "true":
        stage_class = AnswerSummaryChartView
    elif view_data["answer"] is not None:
        stage_class = QuestionSummaryView
    elif stage_data.get("completed_stage") == "start":
        if question.sequential_review:
            stage_class = QuestionSequentialReviewView
        else:
            stage_class = QuestionReviewView
    elif stage_data.get("completed_stage") == "sequential-review":
        stage_class = QuestionReviewView
    else:
        if stage_data.get("datetime_start") is None:
            stage_data.update(
                datetime_start=datetime.now(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )
            )
        if request.GET.get("student_group_assignment_pk", None) is not None:
            stage_data.update(
                student_group_assignment_pk=int(
                    request.GET.get("student_group_assignment_pk")
                )
            )
        stage_class = QuestionStartView

    print(stage_class)
    # Delegate to the view
    stage = stage_class(**view_data)
    try:
        result = stage.dispatch(request)
    except QuestionReload:
        # Something went wrong.  Discard all data and reload.
        stage_data.clear()
        return redirect(request.path)
    stage_data.store()
    return result


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def reset_question(request, assignment_id, question_id):
    """ Clear all answers from user (for testing) """

    assignment = get_object_or_404(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)
    user_token = request.user.username
    answer = get_object_or_none(
        models.Answer,
        assignment=assignment,
        question=question,
        user_token=user_token,
    )
    answer.delete()

    return HttpResponseRedirect(
        reverse(
            "question",
            kwargs={
                "assignment_id": assignment.pk,
                "question_id": question.pk,
            },
        )
    )


# Views related to Teacher
class TeacherBase(LoginRequiredMixin, NoStudentsMixin, View):
    """Base view for Teacher for custom authentication"""

    def dispatch(self, *args, **kwargs):
        if (
            self.request.user
            == get_object_or_404(models.Teacher, pk=kwargs["pk"]).user
        ):

            # Check for any TOS
            if Consent.get(self.request.user.username, "teacher") is None:
                return HttpResponseRedirect(
                    reverse("tos:tos_modify", args=("teacher",))
                    + "?next="
                    + reverse("teacher", args=(kwargs["pk"],))
                )
            else:
                latest_teacher_consent = (
                    Consent.objects.filter(
                        user__username=self.request.user.username,
                        tos__role="teacher",
                    )
                    .order_by("-datetime")
                    .first()
                )
                # Check if TOS is current
                if not latest_teacher_consent.tos.current:
                    return HttpResponseRedirect(
                        reverse("tos:tos_modify", args=("teacher",))
                        + "?next="
                        + reverse("teacher", args=(kwargs["pk"],))
                    )
                else:
                    return super(TeacherBase, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied


class TeacherGroupShare(TeacherBase, DetailView):
    """Share link for a group"""

    model = Teacher
    template_name = "peerinst/teacher/group_details.html"

    def get_object(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        hash = self.kwargs.get("group_hash", None)

        if hash is not None:
            obj = StudentGroup.get(hash)

            if obj is None:
                return response_404(self.request)

            return obj

        else:
            return response_400(self.request)

    def get_context_data(self, **kwargs):
        context = super(TeacherGroupShare, self).get_context_data(**kwargs)
        context["teacher"] = self.teacher

        return context


class TeacherDetailView(TeacherBase, DetailView):
    """Teacher account"""

    model = Teacher
    template_name = "peerinst/teacher/details.html"

    def get_context_data(self, **kwargs):
        context = super(TeacherDetailView, self).get_context_data(**kwargs)
        # provides collection data to collection foldable
        context["owned_collections"] = Collection.objects.filter(
            owner=self.request.user.teacher
        )
        context["LTI_key"] = str(settings.LTI_CLIENT_KEY)
        context["LTI_secret"] = str(settings.LTI_CLIENT_SECRET)
        context["LTI_launch_url"] = str(
            "https://" + self.request.get_host() + "/lti/"
        )
        context["tos_accepted"] = bool(
            Consent.get(self.get_object().user.username, "teacher")
        )

        # To revisit!
        latest_teacher_consent = (
            Consent.objects.filter(
                user__username=self.get_object().user.username,
                tos__role="teacher",
            )
            .order_by("-datetime")
            .first()
        )
        context["tos_timestamp"] = latest_teacher_consent.datetime

        # Set all blink assignments, questions, and rounds for this teacher to
        # inactive
        for a in self.get_object().blinkassignment_set.all():
            if a.active:
                a.active = False
                a.save()

        for b in self.get_object().blinkquestion_set.all():
            if b.active:
                b.active = False
                b.save()

                open_rounds = BlinkRound.objects.filter(question=b).filter(
                    deactivate_time__isnull=True
                )

                for open_round in open_rounds:
                    open_round.deactivate_time = timezone.now()
                    open_round.save()

        return context


class TeacherUpdate(TeacherBase, UpdateView):
    """View for user to update teacher properties"""

    model = Teacher
    fields = ["institutions", "disciplines"]
    template_name = "peerinst/teacher/form.html"


class TeacherAssignments(TeacherBase, ListView):
    """View to modify assignments associated to Teacher"""

    model = Teacher
    template_name = "peerinst/teacher/assignments.html"

    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        return Assignment.objects.all()

    def get_context_data(self, **kwargs):
        context = super(TeacherAssignments, self).get_context_data(**kwargs)
        context["teacher"] = self.teacher
        context["form"] = forms.AssignmentCreateForm()
        context["owned_assignments"] = Assignment.objects.filter(
            owner=self.teacher.user
        )

        return context

    def post(self, request, *args, **kwargs):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        form = forms.TeacherAssignmentsForm(request.POST)
        if form.is_valid():
            assignment = form.cleaned_data["assignment"]
            if assignment in self.teacher.assignments.all():
                self.teacher.assignments.remove(assignment)
            else:
                self.teacher.assignments.add(assignment)
            self.teacher.save()
        else:
            form = forms.AssignmentCreateForm(request.POST)
            if form.is_valid():
                assignment = Assignment(
                    identifier=form.cleaned_data["identifier"],
                    title=form.cleaned_data["title"],
                )
                assignment.save()
                assignment.owner.add(self.teacher.user)
                assignment.save()
                self.teacher.assignments.add(assignment)
                self.teacher.save()
                return HttpResponseRedirect(
                    reverse(
                        "assignment-update",
                        kwargs={"assignment_id": assignment.pk},
                    )
                )
            else:
                return render(
                    request,
                    self.template_name,
                    {
                        "teacher": self.teacher,
                        "form": form,
                        "object_list": Assignment.objects.all(),
                    },
                )

        return HttpResponseRedirect(
            reverse("teacher-assignments", kwargs={"pk": self.teacher.pk})
        )


class TeacherGroups(TeacherBase, ListView):
    """View to modify groups associated to Teacher"""

    model = Teacher
    template_name = "peerinst/teacher/groups.html"

    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        return self.teacher.studentgroup_set.all()

    def get_context_data(self, **kwargs):
        context = super(TeacherGroups, self).get_context_data(**kwargs)
        context["teacher"] = self.teacher
        context["form"] = forms.TeacherGroupsForm()
        context["create_form"] = forms.StudentGroupCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        form = forms.TeacherGroupsForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data["group"]
            if group in self.teacher.current_groups.all():
                self.teacher.current_groups.remove(group)
            else:
                self.teacher.current_groups.add(group)
            self.teacher.save()
        else:
            form = forms.StudentGroupCreateForm(request.POST)
            if form.is_valid():
                form.save()
                form.instance.teacher.add(self.teacher)
                self.teacher.current_groups.add(form.instance)
            else:
                return render(
                    request,
                    self.template_name,
                    {
                        "teacher": self.teacher,
                        "form": forms.TeacherGroupsForm(),
                        "create_form": form,
                        "object_list": self.teacher.studentgroup_set.all(),
                    },
                )

        return HttpResponseRedirect(
            reverse("teacher-groups", kwargs={"pk": self.teacher.pk})
        )


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def teacher_toggle_favourite(request):

    if request.is_ajax():
        # Ajax only
        question = get_object_or_404(Question, pk=request.POST.get("pk"))
        teacher = get_object_or_404(Teacher, user=request.user)
        if question not in teacher.favourite_questions.all():
            teacher.favourite_questions.add(question)
            return JsonResponse({"action": "added"})
        else:
            teacher.favourite_questions.remove(question)
            return JsonResponse({"action": "removed"})
    else:
        return response_400(request)


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def teacher_toggle_follower(request):
    # follow/unfollow heart function
    collection = get_object_or_404(Collection, pk=request.POST.get("pk"))
    teacher = get_object_or_404(Teacher, user=request.user)
    if teacher not in collection.followers.all():
        collection.followers.add(teacher)
        return JsonResponse({"action": "added"})
    else:
        collection.followers.remove(teacher)
        return JsonResponse({"action": "removed"})


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def collection_toggle_assignment(request):
    # add/remove assignment from collection function for hearts on update view
    collection = get_object_or_404(Collection, pk=request.POST.get("ppk"))
    assignment = get_object_or_404(Assignment, pk=request.POST.get("pk"))
    if assignment not in collection.assignments.all():
        collection.assignments.add(assignment)
        return JsonResponse({"action": "added"})
    else:
        collection.assignments.remove(assignment)
        return JsonResponse({"action": "removed"})


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def collection_assign(request):
    # assign button on distribute view
    collection = get_object_or_404(Collection, pk=request.POST.get("ppk"))
    student_group = get_object_or_404(StudentGroup, pk=request.POST.get("pk"))
    is_assigned = False
    for assign in collection.assignments.all():
        if not StudentGroupAssignment.objects.filter(
            group=student_group, assignment=assign
        ).exists():
            is_assigned = True
            StudentGroupAssignment.objects.create(
                group=student_group, assignment=assign
            )
    if is_assigned:
        return JsonResponse({"action": "added"})
    else:
        return JsonResponse({"action": "existing"})


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def collection_unassign(request):
    """
    unassign button on distribute view, assures assignments are not distributed
    """
    collection = get_object_or_404(Collection, pk=request.POST.get("ppk"))
    student_group = get_object_or_404(StudentGroup, pk=request.POST.get("pk"))
    is_unassigned = False
    for assign in collection.assignments.all():
        if StudentGroupAssignment.objects.filter(
            group=student_group, assignment=assign
        ).exists():
            if StudentGroupAssignment.objects.filter(
                group=student_group,
                assignment=assign,
                distribution_date__isnull=True,
            ):
                is_unassigned = True
                StudentGroupAssignment.objects.filter(
                    group=student_group, assignment=assign
                ).delete()
    if is_unassigned:
        return JsonResponse({"action": "removed"})
    else:
        return JsonResponse({"action": "unexisting"})


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def student_activity(request):

    teacher = request.user.teacher

    all_answers_by_group, json_data = get_student_activity_data(
        teacher=teacher
    )

    return TemplateResponse(
        request,
        "peerinst/student_activity.html",
        context={"data": all_answers_by_group, "json": json.dumps(json_data)},
    )


class TeacherBlinks(TeacherBase, ListView):
    """OBSOLETE??"""

    model = Teacher
    template_name = "peerinst/teacher_blinks.html"

    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        return BlinkQuestion.objects.all()  # I don't think this is ever used

    def get_context_data(self, **kwargs):
        context = super(TeacherBlinks, self).get_context_data(**kwargs)
        context["teacher"] = self.teacher

        teacher_discipline_questions = Question.objects.filter(
            discipline__in=self.teacher.disciplines.all()
        )

        teacher_blink_questions = [
            bk.question for bk in self.teacher.blinkquestion_set.all()
        ]
        # Send as context questions not already part of teacher's blinks
        context["suggested_questions"] = [
            q
            for q in teacher_discipline_questions
            if q not in teacher_blink_questions
        ]

        return context

    def post(self, request, *args, **kwargs):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        if request.POST.get("blink", False):
            form = forms.TeacherBlinksForm(request.POST)
            if form.is_valid():
                blink = form.cleaned_data["blink"]
                blink.current = not blink.current
                blink.save()

        if request.POST.get("new_blink", False):
            form = forms.CreateBlinkForm(request.POST)
            if form.is_valid():
                key = random.randrange(10000000, 99999999)
                while key in BlinkQuestion.objects.all():
                    key = random.randrange(10000000, 99999999)
                try:
                    blink = BlinkQuestion(
                        question=form.cleaned_data["new_blink"],
                        teacher=self.teacher,
                        time_limit=60,
                        key=key,
                    )
                    blink.save()
                except Exception:
                    return HttpResponse("error")

        return HttpResponseRedirect(
            reverse("teacher-blinks", kwargs={"pk": self.teacher.pk})
        )


# Views related to Blink


class BlinkQuestionFormView(SingleObjectMixin, FormView):

    form_class = forms.BlinkAnswerForm
    template_name = "peerinst/blink.html"
    model = BlinkQuestion

    def form_valid(self, form):
        self.object = self.get_object()

        try:
            blinkround = BlinkRound.objects.get(
                question=self.object, deactivate_time__isnull=True
            )
        except Exception:
            return TemplateResponse(
                self.request,
                "peerinst/blink_error.html",
                context={
                    "message": "Voting is closed",
                    "url": reverse(
                        "blink-get-current",
                        kwargs={"username": self.object.teacher.user.username},
                    ),
                },
            )

        if self.request.session.get(
            "BQid_" + self.object.key + "_R_" + str(blinkround.id), False
        ):
            return TemplateResponse(
                self.request,
                "peerinst/blink_error.html",
                context={
                    "message": "You may only vote once",
                    "url": reverse(
                        "blink-get-current",
                        kwargs={"username": self.object.teacher.user.username},
                    ),
                },
            )
        else:
            if self.object.active:
                try:
                    models.BlinkAnswer(
                        question=self.object,
                        answer_choice=form.cleaned_data["first_answer_choice"],
                        vote_time=timezone.now(),
                        voting_round=blinkround,
                    ).save()
                    self.request.session[
                        "BQid_" + self.object.key + "_R_" + str(blinkround.id)
                    ] = True
                    self.request.session[
                        "BQid_" + self.object.key
                    ] = form.cleaned_data["first_answer_choice"]
                except Exception:
                    return TemplateResponse(
                        self.request,
                        "peerinst/blink_error.html",
                        context={
                            "message": "Error; try voting again",
                            "url": reverse(
                                "blink-get-current",
                                kwargs={
                                    "username": self.object.teacher.user.username  # noqa
                                },
                            ),
                        },
                    )
            else:
                return TemplateResponse(
                    self.request,
                    "peerinst/blink_error.html",
                    context={
                        "message": "Voting is closed",
                        "url": reverse(
                            "blink-get-current",
                            kwargs={
                                "username": self.object.teacher.user.username
                            },
                        ),
                    },
                )

        return super(BlinkQuestionFormView, self).form_valid(form)

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super(BlinkQuestionFormView, self).get_form_kwargs()
        kwargs.update(answer_choices=self.object.question.get_choices())
        return kwargs

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super(BlinkQuestionFormView, self).get_context_data(**kwargs)
        context["object"] = self.object

        return context

    def get_success_url(self):
        return reverse("blink-summary", kwargs={"pk": self.object.pk})


class BlinkQuestionDetailView(DetailView):

    model = BlinkQuestion

    def get(self, request, *args, **kwargs):
        # Check for an answer... teacher might have refreshed their page and
        # started a new round
        if not request.user.is_authenticated:
            try:
                r = BlinkRound.objects.get(
                    question=self.get_object(), deactivate_time__isnull=True
                )
                if not request.session.get(
                    "BQid_" + self.get_object().key + "_R_" + str(r.id), False
                ):
                    return HttpResponseRedirect(
                        reverse(
                            "blink-question",
                            kwargs={"pk": self.get_object().pk},
                        )
                    )
            except Exception:
                pass

        return super(BlinkQuestionDetailView, self).get(
            request, *args, **kwargs
        )

    def get_context_data(self, **kwargs):
        context = super(BlinkQuestionDetailView, self).get_context_data(
            **kwargs
        )

        # Check if user is a Teacher
        if (
            self.request.user.is_authenticated
            and Teacher.objects.filter(
                user__username=self.request.user
            ).exists()
        ):

            # Check question belongs to this Teacher
            teacher = Teacher.objects.get(user__username=self.request.user)
            if self.object.teacher == teacher:

                # Set all blinks for this teacher to inactive
                for b in teacher.blinkquestion_set.all():
                    b.active = False
                    b.save()

                # Set _this_ question to active in order to accept responses
                self.object.active = True
                if not self.object.time_limit:
                    self.object.time_limit = 60

                time_left = self.object.time_limit
                self.object.save()

                # Close any open rounds
                open_rounds = BlinkRound.objects.filter(
                    question=self.object
                ).filter(deactivate_time__isnull=True)
                for open_round in open_rounds:
                    open_round.deactivate_time = timezone.now()
                    open_round.save()

                # Create round
                r = BlinkRound(
                    question=self.object, activate_time=datetime.now()
                )
                r.save()
            else:
                HttpResponseRedirect(
                    reverse("teacher", kwargs={"pk": teacher.pk})
                )
        else:
            # Get current round, if any
            try:
                r = BlinkRound.objects.get(
                    question=self.object, deactivate_time__isnull=True
                )
                elapsed_time = timezone.now() - r.activate_time
                time_left = max(
                    self.object.time_limit
                    - elapsed_time.seconds
                    - elapsed_time.microseconds / 1e6,
                    0,
                )
            except Exception as e:
                time_left = 0

            # Get latest vote, if any
            context[
                "latest_answer_choice"
            ] = self.object.question.get_choice_label(
                int(self.request.session.get("BQid_" + self.object.key, 0))
            )

        context["teacher"] = self.object.teacher.user.username
        context["round"] = BlinkRound.objects.filter(
            question=self.object
        ).count()
        context["time_left"] = time_left

        return context


@login_required
@require_POST
def blink_assignment_set_time(request, pk):

    form = forms.BlinkSetTimeForm(request.POST)
    blink_assignment = get_object_or_404(models.BlinkAssignment, key=pk)
    if form.is_valid():
        for blink_question in blink_assignment.blinkquestions.all():
            blink_question.time_limit = form.cleaned_data["time_limit"]
            blink_question.save()

    return HttpResponseRedirect(
        reverse("blinkAssignment-start", kwargs={"pk": pk})
    )


@login_required
def blink_assignment_start(request, pk):
    """View to start a blink script"""

    # Check this user is a Teacher and owns this assignment
    try:
        teacher = Teacher.objects.get(user__username=request.user)
        blinkassignment = BlinkAssignment.objects.get(key=pk)

        if blinkassignment.teacher == teacher:

            # Deactivate all blinkAssignments
            for a in teacher.blinkassignment_set.all():
                a.active = False
                a.save()

            # Activate _this_ blinkAssignment
            blinkassignment.active = True
            blinkassignment.save()

            return HttpResponseRedirect(
                reverse(
                    "blink-summary",
                    kwargs={
                        "pk": blinkassignment.blinkquestions.order_by(
                            "blinkassignmentquestion__rank"
                        )
                        .first()
                        .pk
                    },
                )
            )

        else:
            return TemplateResponse(
                request,
                "peerinst/blink_error.html",
                context={
                    "message": "Assignment does not belong to this teacher",
                    "url": reverse("teacher", kwargs={"pk": teacher.pk}),
                },
            )

    except Exception:
        return TemplateResponse(
            request,
            "peerinst/blink_error.html",
            context={"message": "Error", "url": reverse("logout")},
        )


@login_required
def blink_assignment_delete(request, pk):
    """View to delete a blink script"""

    # Check this user is a Teacher and owns this assignment
    try:
        teacher = Teacher.objects.get(user__username=request.user)
        blinkassignment = BlinkAssignment.objects.get(key=pk)

        if blinkassignment.teacher == teacher:

            # Delete
            blinkassignment.delete()

            return HttpResponseRedirect(
                reverse("teacher", kwargs={"pk": teacher.pk})
            )

        else:
            return TemplateResponse(
                request,
                "peerinst/blink_error.html",
                context={
                    "message": "Assignment does not belong to this teacher",
                    "url": reverse("teacher", kwargs={"pk": teacher.pk}),
                },
            )

    except Exception:
        return TemplateResponse(
            request,
            "peerinst/blink_error.html",
            context={"message": "Error", "url": reverse("logout")},
        )


def blink_get_next(request, pk):
    """
    View to process next question in a series of blink questions based on
    state.
    """

    try:
        # Get BlinkQuestion
        blinkquestion = BlinkQuestion.objects.get(pk=pk)
        # Get Teacher (should only ever be one object returned)
        teacher = blinkquestion.teacher
        # Check the active BlinkAssignment, if any
        blinkassignment = teacher.blinkassignment_set.get(active=True)
        # Get rank of question in list
        for q in blinkassignment.blinkassignmentquestion_set.all():
            if q.blinkquestion == blinkquestion:
                rank = q.rank
                break
        # Redirect to next, if exists
        if rank < blinkassignment.blinkassignmentquestion_set.count() - 1:

            try:
                # Teacher to new summary page
                # Check existence of teacher (exception thrown otherwise)
                return HttpResponseRedirect(
                    reverse(
                        "blink-summary",
                        kwargs={
                            "pk": blinkassignment.blinkassignmentquestion_set.get(  # noqa
                                rank=rank + 1
                            ).blinkquestion.pk
                        },
                    )
                )
            except Exception:
                # Others to new question page
                return HttpResponseRedirect(
                    reverse(
                        "blink-question",
                        kwargs={
                            "pk": blinkassignment.blinkassignmentquestion_set.get(  # noqa
                                rank=rank + 1
                            ).blinkquestion.pk
                        },
                    )
                )

        else:
            blinkassignment.active = False
            blinkassignment.save()
            return HttpResponseRedirect(
                reverse("teacher", kwargs={"pk": teacher.pk})
            )

    except Exception:
        return HttpResponse("Error")


def blink_get_current(request, username):
    """View to redirect user to latest active BlinkQuestion for teacher."""

    try:
        # Get teacher
        teacher = Teacher.objects.get(user__username=username)
    except Exception:
        return HttpResponse("Teacher does not exist")

    # Only teacher that owns this script can access page while logged in
    if request.user != teacher.user:
        logout(request)

    try:
        # Redirect to current active blinkquestion, if any, if this user has
        # not voted yet in this round
        blinkquestion = teacher.blinkquestion_set.get(active=True)
        blinkround = blinkquestion.blinkround_set.latest("activate_time")
        if request.session.get(
            "BQid_" + blinkquestion.key + "_R_" + str(blinkround.id), False
        ):
            return HttpResponseRedirect(
                reverse("blink-summary", kwargs={"pk": blinkquestion.pk})
            )
        else:
            return HttpResponseRedirect(
                reverse("blink-question", kwargs={"pk": blinkquestion.pk})
            )
    except Exception:
        # Else, redirect to summary for last active question latest_round =
        # BlinkRound.objects.filter(question__in=teacher.blinkquestion_set.all()).latest('activate_time')
        # return HttpResponseRedirect(reverse('blink-summary', kwargs={'pk' :
        # latest_round.question.pk})) Else, redirect to waiting room
        return HttpResponseRedirect(
            reverse(
                "blink-waiting", kwargs={"username": teacher.user.username}
            )
        )


def blink_waiting(request, username, assignment=""):

    try:
        teacher = Teacher.objects.get(user__username=username)
    except Exception:
        return HttpResponse("Error")

    # Only teacher that owns this script can access page while logged in
    if request.user != teacher.user:
        logout(request)

    return TemplateResponse(
        request,
        "peerinst/blink_waiting.html",
        context={
            "assignment": assignment,
            "teacher": teacher,
            "form": forms.BlinkSetTimeForm(),
        },
    )


def collection_search(request):
    if not Teacher.objects.filter(user=request.user).exists():
        return HttpResponse(
            _(
                "You must be logged in as a teacher to search the database. "
                "Log in again with a teacher account."
            )
        )

    if request.method == "GET" and request.user.is_authenticated:
        page = request.GET.get("page", default=1)
        type = request.GET.get("type", default=None)
        id = request.GET.get("id", default=None)
        search_string = request.GET.get("search_string", default="")
        limit_search = request.GET.get("limit_search", default="false")
        authors = request.GET.getlist("author", default=None)
        disciplines = request.GET.getlist("discipline", default=None)

        q_obj = Q()
        if authors[0]:
            q_obj &= Q(
                owner__in=Teacher.objects.filter(
                    user__in=User.objects.filter(username__in=authors)
                )
            )
        if disciplines[0]:
            q_obj &= Q(
                discipline__in=Discipline.objects.filter(title__in=disciplines)
            )
        q_obj &= Q(private=False)
        is_english = get_language() == "en"
        # All matching collections
        search_list = Collection.objects.filter(q_obj)

        search_string_split_list = search_string.split()
        for string in search_string.split():
            if is_english and string in en:
                search_string_split_list.remove(string)
            elif not is_english and string in fr:
                search_string_split_list.remove(string)
        search_terms = [search_string]
        if len(search_string_split_list) > 1:
            search_terms.extend(search_string_split_list)

        query = []
        query_all = []
        # by searching first for full string, and then for constituent parts,
        # and preserving order, the results should rank the items higher to the
        # top that have the entire search_string included
        query_meta = {}
        for term in search_terms:
            query_term = collection_search_function(term, search_list)

            query_term = [q for q in query_term if q not in query_all]

            query_meta[term] = query_term

            query_all.extend(query_term)

        paginator = Paginator(query_all, 50)
        try:
            query_subset = paginator.page(page)
        except PageNotAnInteger:
            query_subset = paginator.page(1)
        except EmptyPage:
            query_subset = paginator.page(paginator.num_pages)

        query = []

        for term in list(query_meta.keys()):
            query_dict = {}
            query_dict["term"] = term
            query_dict["collections"] = [
                q for q in query_meta[term] if q in query_subset.object_list
            ]
            query_dict["count"] = len(query_dict["collections"])
            query.append(query_dict)

        return TemplateResponse(
            request,
            "peerinst/collection/search_results.html",
            context={
                "paginator": query_subset,
                "search_results": query,
                "count": len(query_all),
                "previous_search_string": search_terms,
                "type": type,
            },
        )
    else:
        return HttpResponse(
            _("An error occurred.  Retry search after logging in again.")
        )


def collection_search_function(search_string, pre_filtered_list=None):

    query_result = pre_filtered_list.filter(
        Q(title__icontains=search_string)
        | Q(description__icontains=search_string)
    )

    return query_result


# AJAX functions
def question_search(request):

    if not Teacher.objects.filter(user=request.user).exists():
        return HttpResponse(
            _(
                "You must be logged in as a teacher to search the database. "
                "Log in again with a teacher account."
            )
        )

    if request.method == "GET" and request.user.is_authenticated:
        page = request.GET.get("page", default=1)
        type = request.GET.get("type", default=None)
        id = request.GET.get("id", default=None)
        search_string = request.GET.get("search_string", default="")
        limit_search = request.GET.get("limit_search", default="false")
        authors = request.GET.getlist("author", default=None)
        disciplines = request.GET.getlist("discipline", default=None)
        subjects = request.GET.getlist("subject", default=None)
        categories = request.GET.getlist("category", default=None)

        # Exclusions based on type of search
        q_qs = []
        if type == "blink":
            assignment = None
            bq_qs = request.user.teacher.blinkquestion_set.all()
            q_qs = [bq.question.id for bq in bq_qs]
            form_field_name = "new_blink"

        if type == "assignment":
            assignment = Assignment.objects.get(
                identifier=request.GET["assignment_identifier"]
            )
            a_qs = Assignment.objects.get(identifier=id).questions.all()
            t_qs = request.user.teacher.favourite_questions.all()
            q_qs = [q.id for q in a_qs]
            q_qs.extend([q.id for q in t_qs])
            form_field_name = "q"

        if type is None:
            assignment = None
            q_qs = []
            form_field_name = None

        # Establish pool of questions for search
        q_obj = Q()
        if authors and authors[0]:
            q_obj &= Q(
                Q(user__in=User.objects.filter(username__in=authors))
                | Q(
                    collaborators__in=User.objects.filter(username__in=authors)
                )
            )
        if disciplines and disciplines[0]:
            q_obj &= Q(
                discipline__in=Discipline.objects.filter(title__in=disciplines)
            )
        if categories and categories[0]:
            if subjects and subjects[0]:
                q_obj &= Q(
                    category__in=Category.objects.filter(
                        Q(title__in=categories)
                        | Q(
                            subjects__in=Subject.objects.filter(
                                title__in=subjects
                            )
                        )
                    ).distinct()
                )
            else:
                q_obj &= Q(
                    category__in=Category.objects.filter(title__in=categories)
                )
        elif subjects and subjects[0]:
            q_obj &= Q(
                category__in=Category.objects.filter(
                    Q(subjects__in=Subject.objects.filter(title__in=subjects))
                ).distinct()
            )
        search_list = Question.unflagged_objects.filter(q_obj)
        if categories and subjects and categories[0] and subjects[0]:
            search_list = search_list.filter(
                category__in=Category.objects.filter(title__in=categories)
            )

        if limit_search == "true":
            search_list = search_list.filter(
                discipline__in=request.user.teacher.disciplines.all()
            )

        # if meta_search:
        #    search_list = filter(meta_search, search_list)
        is_english = get_language() == "en"
        # All matching questions

        search_string_split_list = search_string.split()
        for string in search_string.split():
            if is_english and string in en:
                search_string_split_list.remove(string)
            elif not is_english and string in fr:
                search_string_split_list.remove(string)
        search_terms = [search_string]
        if len(search_string_split_list) > 1:
            search_terms.extend(search_string_split_list)

        query = []
        query_all = []
        # by searching first for full string, and then for constituent parts,
        # and preserving order, the results should rank the items higher to the
        # top that have the entire search_string included
        query_meta = {}
        for term in search_terms:
            query_term = question_search_function(
                term, search_list, (type == "assignment" or type == "blink")
            )
            query_term = query_term.exclude(id__in=q_qs).distinct()

            query_term = [
                q
                for q in query_term
                if q not in query_all
                and (q.answerchoice_set.count() > 0 or q.type == "RO")
            ]

            query_meta[term] = query_term

            query_all.extend(query_term)

        paginator = Paginator(query_all, 50)
        try:
            query_subset = paginator.page(page)
        except PageNotAnInteger:
            query_subset = paginator.page(1)
        except EmptyPage:
            query_subset = paginator.page(paginator.num_pages)

        query = []

        for term in list(query_meta.keys()):
            query_dict = {}
            query_dict["term"] = term
            query_dict["questions"] = [
                q for q in query_meta[term] if q in query_subset.object_list
            ]
            query_dict["count"] = len(query_dict["questions"])
            query.append(query_dict)

        return TemplateResponse(
            request,
            "peerinst/question/search_results.html",
            context={
                "paginator": query_subset,
                "search_results": query,
                "form_field_name": form_field_name,
                "count": len(query_all),
                "previous_search_string": search_terms,
                "assignment": assignment,
                "type": type,
            },
        )
    else:
        return HttpResponse(
            _("An error occurred.  Retry search after logging in again.")
        )


def blink_get_current_url(request, username):
    """View to check current question url for teacher."""

    try:
        # Get teacher
        teacher = Teacher.objects.get(user__username=username)
    except Exception:
        return HttpResponse("Teacher does not exist")

    try:
        # Return url of current active blinkquestion, if any
        blinkquestion = teacher.blinkquestion_set.get(active=True)
        url = reverse("blink-question", kwargs={"pk": blinkquestion.pk})
        return JsonResponse({"action": url})
    except Exception:
        if not teacher.blinkassignment_set.filter(active=True).exists():
            return JsonResponse({"action": "stop"})
        try:
            latest_round = BlinkRound.objects.filter(
                question__in=teacher.blinkquestion_set.all()
            ).latest("activate_time")
            url = reverse(
                "blink-summary", kwargs={"pk": latest_round.question.pk}
            )
            return JsonResponse({"action": url})
        except Exception:
            return JsonResponse({"action": "stop"})


def blink_count(request, pk):

    blinkquestion = BlinkQuestion.objects.get(pk=pk)
    try:
        blinkround = BlinkRound.objects.get(
            question=blinkquestion, deactivate_time__isnull=True
        )
    except Exception:
        try:
            blinkround = BlinkRound.objects.filter(
                question=blinkquestion
            ).latest("deactivate_time")
        except Exception:
            return JsonResponse()

    context = {}
    context["count"] = BlinkAnswer.objects.filter(
        voting_round=blinkround
    ).count()

    return JsonResponse(context)


def blink_close(request, pk):

    context = {}

    if request.method == "POST" and request.user.is_authenticated:
        form = forms.BlinkQuestionStateForm(request.POST)
        try:
            blinkquestion = BlinkQuestion.objects.get(pk=pk)
            blinkround = BlinkRound.objects.get(
                question=blinkquestion, deactivate_time__isnull=True
            )
            if form.is_valid():
                blinkquestion.active = form.cleaned_data["active"]
                blinkquestion.save()
                blinkround.deactivate_time = timezone.now()
                blinkround.save()
                context["state"] = "success"
            else:
                context["state"] = "failure"
        except Exception:
            context["state"] = "failure"

    return JsonResponse(context)


def blink_latest_results(request, pk):

    results = {}

    blinkquestion = BlinkQuestion.objects.get(pk=pk)
    blinkround = BlinkRound.objects.filter(question=blinkquestion).latest(
        "deactivate_time"
    )

    c = 1
    for label, text in blinkquestion.question.get_choices():
        results[label] = (
            BlinkAnswer.objects.filter(question=blinkquestion)
            .filter(voting_round=blinkround)
            .filter(answer_choice=c)
            .count()
        )
        c = c + 1

    return JsonResponse(results)


def blink_status(request, pk):

    blinkquestion = BlinkQuestion.objects.get(pk=pk)

    response = {}
    response["status"] = blinkquestion.active

    return JsonResponse(response)


# This is a very temporary approach with minimum checking for permissions
@login_required
def blink_reset(request, pk):

    # blinkquestion = BlinkQuestion.objects.get(pk=pk)

    return HttpResponseRedirect(reverse("blink-summary", kwargs={"pk": pk}))


class BlinkAssignmentCreate(LoginRequiredMixin, CreateView):

    model = BlinkAssignment
    fields = ["title"]

    def form_valid(self, form):
        key = random.randrange(10000000, 99999999)
        while key in BlinkAssignment.objects.all():
            key = random.randrange(10000000, 99999999)
        form.instance.key = key
        form.instance.teacher = Teacher.objects.get(user=self.request.user)
        return super(BlinkAssignmentCreate, self).form_valid(form)

    def get_success_url(self):
        if Teacher.objects.filter(user=self.request.user).exists():
            return reverse(
                "blinkAssignment-update", kwargs={"pk": self.object.id}
            )
        else:
            return reverse("welcome")


class BlinkAssignmentUpdate(LoginRequiredMixin, DetailView):

    model = BlinkAssignment

    def get_context_data(self, **kwargs):
        context = super(BlinkAssignmentUpdate, self).get_context_data(**kwargs)
        context["teacher"] = Teacher.objects.get(user=self.request.user)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user.is_authenticated:
            form = forms.RankBlinkForm(request.POST)
            if form.is_valid():

                # Questions can appear in multiple assignments, but only once
                # in each.  Get Q for _this_ assignment.
                relationship = form.cleaned_data["q"].get(
                    blinkassignment=self.object
                )
                operation = form.cleaned_data["rank"]
                if operation == "down":
                    relationship.move_down_rank()
                    relationship.save()
                if operation == "up":
                    relationship.move_up_rank()
                    relationship.save()
                if operation == "clear":
                    relationship.delete()
                    relationship.renumber()

                return HttpResponseRedirect(
                    reverse(
                        "blinkAssignment-update", kwargs={"pk": self.object.pk}
                    )
                )
            else:
                form = forms.CreateBlinkForm(request.POST)
                if form.is_valid():
                    question = form.cleaned_data["new_blink"]
                    key = random.randrange(10000000, 99999999)
                    while key in BlinkQuestion.objects.all():
                        key = random.randrange(10000000, 99999999)
                    try:
                        blinkquestion = BlinkQuestion(
                            question=question,
                            teacher=Teacher.objects.get(
                                user=self.request.user
                            ),
                            time_limit=30,
                            key=key,
                        )
                        blinkquestion.save()

                        if (
                            blinkquestion
                            not in self.object.blinkquestions.all()
                        ):
                            relationship = BlinkAssignmentQuestion(
                                blinkassignment=self.object,
                                blinkquestion=blinkquestion,
                                rank=self.object.blinkquestions.count(),
                            )
                        relationship.save()
                    except Exception:
                        return HttpResponse("error")

                    return HttpResponseRedirect(
                        reverse(
                            "blinkAssignment-update",
                            kwargs={"pk": self.object.pk},
                        )
                    )
                else:
                    form = forms.AddBlinkForm(request.POST)
                    if form.is_valid():
                        blinkquestion = form.cleaned_data["blink"]
                        if (
                            blinkquestion
                            not in self.object.blinkquestions.all()
                        ):
                            relationship = BlinkAssignmentQuestion(
                                blinkassignment=self.object,
                                blinkquestion=blinkquestion,
                                rank=self.object.blinkquestions.count(),
                            )
                            relationship.save()
                        else:
                            return HttpResponse("error")

                        return HttpResponseRedirect(
                            reverse(
                                "blinkAssignment-update",
                                kwargs={"pk": self.object.pk},
                            )
                        )
                    else:
                        return HttpResponse("error")
        else:
            return HttpResponse("error3")


class DateExtractFunc(Func):
    function = "DATE"


def assignment_timeline_data(request, assignment_id, question_id):
    qs = (
        models.Answer.objects.filter(assignment_id=assignment_id)
        .filter(question_id=question_id)
        .annotate(date=DateExtractFunc("datetime_first"))
        .values("date")
        .annotate(N=Count("id"))
    )

    return JsonResponse(list(qs), safe=False)


def network_data(request, assignment_id):
    qs = models.Answer.objects.filter(assignment_id=assignment_id)

    links = {}

    for answer in qs:
        if answer.user_token not in links:
            links[answer.user_token] = {}
            if answer.chosen_rationale:
                if (
                    answer.chosen_rationale.user_token
                    in links[answer.user_token]
                ):
                    links[answer.user_token][
                        answer.chosen_rationale.user_token
                    ] += 1
                else:
                    links[answer.user_token][
                        answer.chosen_rationale.user_token
                    ] = 1

    # serialize
    links_array = []
    for source, targets in list(links.items()):
        d = {}
        for t in list(targets.keys()):
            d["source"] = source
            d["target"] = t
            d["value"] = targets[t]
            links_array.append(d)

    return JsonResponse(links_array, safe=False)


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def report_selector(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    return TemplateResponse(
        request,
        "peerinst/teacher/report_selector.html",
        {
            "report_select_form": forms.ReportSelectForm(
                teacher_username=teacher.user.username
            ),
            "teacher_id": teacher.id,
        },
    )


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def report(request, assignment_id="", group_id=""):
    template_name = "peerinst/report_all_rationales.html"
    teacher = get_object_or_404(Teacher, user=request.user)

    if not request.GET:
        return HttpResponseRedirect(reverse("report_selector"))

    if request.GET.getlist("student_groups"):
        student_groups = request.GET.getlist("student_groups")
    elif group_id:
        student_groups = [
            StudentGroup.objects.get(name=urllib.parse.unquote(group_id)).pk
        ]
    else:
        student_groups = teacher.current_groups.all().values_list("pk")

    if request.GET.getlist("assignments"):
        assignment_list = request.GET.getlist("assignments")
    elif assignment_id:
        assignment_list = [urllib.parse.unquote(assignment_id)]
    else:
        assignment_list = teacher.assignments.all().values_list(
            "identifier", flat=True
        )

    assignment_data = report_data_by_assignment(
        assignment_list, student_groups, teacher
    )

    context = {}
    context["data"] = assignment_data

    ######
    # for aggregate gradebook over all assignments

    gradebook_student = report_data_by_student(assignment_list, student_groups)
    gradebook_question = report_data_by_question(
        assignment_list, student_groups
    )

    # needs DRY
    metric_labels = ["N", "RR", "RW", "WR", "WW"]
    question_list = Question.objects.filter(
        assignment__identifier__in=assignment_list
    ).values_list("title", flat=True)

    context["gradebook_student"] = gradebook_student
    context["gradebook_question"] = gradebook_question
    context["gradebook_keys"] = metric_labels
    context["question_list"] = question_list
    context["teacher"] = teacher
    # context["json"] = json.dumps(d3_data)

    return render(request, template_name, context)


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def report_assignment_aggregates(request):
    """
    - wrapper for admin_views.get_question_rationale_aggregates
    - use student_groups and assignment_list passed through request.GET, and
      return JsonReponse as data for report
    """

    student_groups = request.GET.getlist("student_groups")
    assignment_list = request.GET.getlist("assignments")

    j = []
    for a_str in assignment_list:
        a = Assignment.objects.get(identifier=a_str)
        d_a = {}
        d_a["assignment"] = a.identifier
        d_a["questions"] = []
        for q in a.questions.all():
            d_q = {}
            d_q["question"] = q.text
            try:
                d_q["question_image_url"] = q.image.url
            except ValueError:
                pass
            d_q["influential_rationales"] = []
            sums, output = get_question_rationale_aggregates(
                assignment=a,
                question=q,
                perpage=50,
                student_groups=student_groups,
            )
            for trx, rationale_list in list(output.items()):
                d_q_i = {}
                d_q_i["transition_type"] = trx
                d_q_i["rationales"] = []
                # d_q_i['total_count'] = sums[trx]
                for r in rationale_list:
                    d_q_i_r = {}
                    d_q_i_r["count"] = r["count"]
                    if r["rationale"]:
                        d_q_i_r["rationale"] = r["rationale"].rationale
                    else:
                        d_q_i_r["rationale"] = "Chose own rationale"
                    d_q_i["rationales"].append(d_q_i_r)
                d_q["influential_rationales"].append(d_q_i)
            d_a["questions"].append(d_q)
        j.append(d_a)

    return JsonResponse(j, safe=False)


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def connect_group_to_course(request):

    course_pk = request.POST.get("course_pk")
    student_group = StudentGroup.objects.get(pk=request.POST.get("group_pk"))

    students_as_students = student_group.students.values_list(
        "student", flat=True
    )
    students_as_users = User.objects.filter(pk__in=students_as_students)

    clone = setup_link_to_group(course_pk, students_as_users)

    try:
        StudentGroupCourse.objects.create(
            course=clone, student_group=student_group
        )
    except ValidationError:
        return JsonResponse({"action": "error"})

    date = clone.created_on.strftime("%b. %d, %Y, %I:%S %p")

    return JsonResponse(
        {
            "action": "posted",
            "linked_course_pk": clone.pk,
            "linked_course_title": clone.title,
            "linked_course_created_date": date,
        }
    )


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def disconnect_group_from_course(request):

    course_pk = request.POST.get("course_pk")

    try:
        setup_unlink_from_group(course_pk)
    except ValidationError:
        return JsonResponse({"action": "error"})

    return JsonResponse({"action": "posted"})
