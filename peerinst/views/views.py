import json
import logging
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

import bleach
import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

# reports
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.db.models.expressions import Func
from django.db.models.fields import IntegerField
from django.forms import Textarea, inlineformset_factory
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_safe
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView
from lti_provider.lti import LTI
from pylti.common import post_message
from tinymce.widgets import TinyMCE

from dalite.views.errors import response_400, response_404
from peerinst import admin, forms, models, rationale_choice
from peerinst.admin_views import get_question_rationale_aggregates
from peerinst.elasticsearch import assignment_search as as_ES
from peerinst.elasticsearch import collection_search as cs_ES
from peerinst.elasticsearch import question_search as qs_ES
from peerinst.mixins import (
    LoginRequiredMixin,
    NoStudentsMixin,
    ObjectPermissionMixin,
    TOSAcceptanceRequiredMixin,
    student_check,
    teacher_tos_accepted_check,
)
from peerinst.models import (
    Answer,
    AnswerChoice,
    Assignment,
    AssignmentQuestions,
    Category,
    Collection,
    Discipline,
    NewUserRequest,
    Question,
    RationaleOnlyQuestion,
    SaltiseMember,
    ShownRationale,
    Student,
    StudentGroup,
    StudentGroupAssignment,
    Subject,
    Teacher,
    UserType,
    UserUrl,
)
from peerinst.stopwords import en, fr
from peerinst.tasks import mail_managers_async
from peerinst.templatetags.bleach_html import STRICT_TAGS
from peerinst.util import (
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

# tos
from tos.models import Consent, Tos

from .decorators import ajax_login_required, ajax_user_passes_test

LOGGER = logging.getLogger(__name__)
LOGGER_teacher_activity = logging.getLogger("teacher_activity")
performance_logger = logging.getLogger("performance")
search_logger = logging.getLogger("search")
logger_auth = logging.getLogger("peerinst-auth")


# Views related to Auth
@require_safe
def landing_page(request):
    disciplines = {}

    disciplines["All"] = {}
    disciplines["All"]["questions"] = Question.objects.count()
    disciplines["All"]["rationales"] = Answer.objects.count()
    disciplines["All"]["students"] = Student.objects.count()
    disciplines["All"]["teachers"] = Teacher.objects.count()

    for d in Discipline.objects.annotate(num_q=Count("question")).order_by(
        "-num_q"
    )[:3]:
        disciplines[str(d.title)] = {}
        disciplines[str(d.title)]["questions"] = Question.objects.filter(
            discipline=d
        ).count()
        disciplines[str(d.title)]["rationales"] = Answer.objects.filter(
            question__discipline=d
        ).count()

        question_list = d.question_set.values_list("id", flat=True)
        disciplines[str(d.title)]["students"] = len(
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
    d2["name"] = "All"
    d2["questions"] = Question.objects.count()
    d2["rationales"] = Answer.objects.count()
    d2["students"] = Student.objects.count()
    d2["teachers"] = Teacher.objects.count()

    disciplines_array.append(d2)

    for d in Discipline.objects.annotate(num_q=Count("question")).order_by(
        "-num_q"
    )[:3]:
        d2 = {}
        d2["name"] = str(d.title)
        d2["questions"] = Question.objects.filter(discipline=d).count()
        d2["rationales"] = Answer.objects.filter(
            question__discipline=d
        ).count()

        question_list = d.question_set.values_list("id", flat=True)
        disciplines[str(d.title)]["students"] = len(
            set(
                Answer.objects.filter(question_id__in=question_list)
                .exclude(user_token="")
                .values_list("user_token", flat=True)
            )
        )

        d2["teachers"] = d.teacher_set.count()

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

            # TODO: Adapt to different types of user
            NewUserRequest.objects.create(
                user=form.instance, type=UserType.objects.get(type="teacher")
            )
            UserUrl.objects.create(
                user=form.instance, url=form.cleaned_data["url"]
            )

            # Notify managers
            email_context = {
                "date": timezone.now(),
                "email": form.cleaned_data["email"],
                "url": form.cleaned_data["url"],
                "site_name": "myDALITE",
            }
            mail_managers_async(
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


def page_not_found(request):
    raise Http404("")


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
        return HttpResponseRedirect(reverse("saltise:lobby"))

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


class QuestionListView(LoginRequiredMixin, NoStudentsMixin, ListView):
    """List of questions used for debugging purposes."""

    model = models.Assignment
    template_name = "peerinst/question/list.html"

    def get_queryset(self):
        self.assignment = get_object_or_404(
            models.Assignment, pk=self.kwargs["assignment_id"]
        )
        return self.assignment.questions.order_by("assignmentquestions__rank")

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)
        context.update(assignment=self.assignment)
        return context


class AssignmentFixView(
    LoginRequiredMixin, NoStudentsMixin, TOSAcceptanceRequiredMixin, DetailView
):
    """
    Assignment is not fixable if:
    - Any question is flagged and assignment is not editable by user;
    - Any question is missing answer choices and is not editable or user is not
      owner;
    """

    model = models.Assignment
    template_name = "peerinst/question/fix.html"

    def get_context_data(self, **kwargs):
        broken_by_flags = Question.is_flagged(self.object.questions.all())

        broken_by_answerchoices = Question.is_missing_answer_choices(
            self.object.questions.all()
        )

        context = super().get_context_data(**kwargs)
        context.update(
            assignment=True,
            broken_by_flags=broken_by_flags,
            broken_by_answerchoices=broken_by_answerchoices,
            load_url=f"{reverse('REST:question-list')}?q={'&q='.join(str(q.pk) for q in self.object.questions.all())}",  # noqa
            teacher=self.request.user.teacher,
        )
        return context


class QuestionFixView(
    LoginRequiredMixin, NoStudentsMixin, TOSAcceptanceRequiredMixin, DetailView
):
    model = models.Question
    template_name = "peerinst/question/fix.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            load_url=f"{reverse('REST:question-list')}?q={self.object.pk}",
            teacher=self.request.user.teacher,
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
        if not self.object.is_editable:
            return None
        form = super().get_form(form_class)
        form.fields["text"].widget = TinyMCE()
        return form

    def post(self, request, *args, **kwargs):
        # Check if student answers exist
        if not self.get_object().is_editable:
            raise PermissionDenied
        else:
            return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Only owner can update collaborators
        if self.object.user != self.request.user:
            form.cleaned_data[
                "collaborators"
            ] = self.object.collaborators.all()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        if not question.is_editable:
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
                        if a.is_editable and question not in a.questions.all():
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


class QuestionMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            assignment=self.assignment,
            question=self.question,
            answer_choices=self.answer_choices,
            correct=self.question.answerchoice_set.filter(correct=True),
            experts=self.question.answer_set.filter(expert=True),
        )

        # Pass hints so that template knows context

        if self.request.session.get("access_type") == StudentGroup.STANDALONE:
            context.update(access_standalone=True)
        elif (
            self.request.session.get("access_type")
            == StudentGroup.LTI_STANDALONE
        ):
            context.update(access_lti_standalone=True)
        elif self.request.session.get("access_type") == StudentGroup.LTI:
            context.update(access_lti_basic_client_key=True)
        else:
            context.update(access_teacher=True)

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
            assignment_expired=self.request.session.get("assignment_expired")
        )
        context.update(quality=self.request.session.get("quality"))

        return context

    def send_grade(self):
        if self.request.session.get("access_type") != StudentGroup.LTI:
            # We are running outside of a basic LTI context, so we don't need to
            # send a grade.
            return
        else:
            redirect_url = reverse(
                "question",
                kwargs={
                    "assignment_id": self.assignment.pk,
                    "question_id": self.question.id,
                },
            )
            launch_url = None
            lti = LTI(request_type="any", role_type="any")
            user = authenticate(request=self.request, lti=lti)
            login(
                self.request,
                user,
                backend="peerinst.lti.LTIBackendStudentsOnly",
            )

            xml = lti.generate_request_xml(
                message_identifier_id=f"{time.time():.0f}",
                operation="replaceResult",
                lis_result_sourcedid=lti.lis_result_sourcedid(self.request),
                score=self.answer.grade,
                launch_url=launch_url,
            )

            try:
                post_message(
                    consumers=lti.consumers(),
                    lti_key=lti.oauth_consumer_key(self.request),
                    url=lti.lis_outcome_service_url(self.request),
                    body=xml,
                )
                logger_auth.info(
                    f"Grade of {self.answer.grade} posted for {lti.user_id(self.request)} in course {lti.course_context(self.request)} to {lti.lis_outcome_service_url(self.request)}"  # noqa
                )
            except Exception as e:
                logger_auth.error(
                    f"Failure '{e}' while posting grade of {self.answer.grade} for {lti.user_id(self.request)} in course {lti.course_context(self.request)} to {lti.lis_outcome_service_url(self.request)}"  # noqa
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
                return super().dispatch(*args, **kwargs)

    def emit_event(self, name, **data):
        """
        Log an event in a JSON format for each step in problem
        """
        # Add common fields to event data
        data.update(
            assignment_id=self.assignment.pk if self.assignment else None,
            assignment_title=self.assignment.title
            if self.assignment
            else None,
            question_id=self.question.pk,
            question_text=self.question.text,
        )

        # Build event dictionary
        META = self.request.META
        event = {
            "accept_language": META.get("HTTP_ACCEPT_LANGUAGE"),
            "agent": META.get("HTTP_USER_AGENT"),
            "course_id": self.request.session.get("context_id", ""),
            "event": data,
            "event_type": name,
            "host": META.get("SERVER_NAME"),
            "ip": META.get("HTTP_X_REAL_IP", META.get("REMOTE_ADDR")),
            "referer": META.get("HTTP_REFERER"),
            "time": datetime.now().isoformat(),
            "username": self.user_token,
        }

        # Write JSON to log file
        LOGGER.info(json.dumps(event))

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
    """
    Render a question with or without answer choices depending on type.

    The user can choose one answer and enter a rationale.
    """

    template_name = "peerinst/question/start.html"

    def get_form_class(self):
        return self.question.get_start_form_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(answer_choices=self.answer_choices)
        if self.request.method == "GET":
            # Log when the page is first shown, mainly for the timestamp.
            self.emit_event("problem_show")
        return kwargs

    def form_valid(self, form):
        self.question.start_form_valid(self, form)

        return super().form_valid(form)


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
            (
                self.user_token,
                self.assignment.pk if self.assignment else None,
                self.question.pk,
            )
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
            self.mark_rationales_safe(escape_html=False)
        self.stage_data.update(rationale_choices=self.rationale_choices)

    def mark_rationales_safe(self, escape_html):
        processor = escape if escape_html else mark_safe
        for _choice, _label, rationales, _text in self.rationale_choices:
            rationales[:] = [
                (
                    id,
                    processor(
                        bleach.clean(
                            text,
                            tags=STRICT_TAGS,
                            strip=True,
                        )
                    ),
                )
                for id, text in rationales
            ]

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
        for _choice, _label, rationales, _text in self.rationale_choices:
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
        kwargs = super().get_form_kwargs()
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
        context = super().get_context_data(**kwargs)
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
                for choice, label, rationales, text in self.rationale_choices
            )
        )
        self.current_rationale = rationale_sequence[0]
        self.stage_data.update(
            rationale_sequence=rationale_sequence,
            rationale_votes={},
            rationale_index=0,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return super().form_valid(form)


class QuestionReviewView(QuestionReviewBaseView):
    """
    The standard version of the review, showing all alternative rationales
    simultaneously.
    """

    template_name = "peerinst/question/review.html"
    form_class = forms.ReviewAnswerForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
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
        return super().form_valid(form)

    def emit_check_events(self):
        grade = self.answer.grade
        event_data = {
            "second_answer_choice": self.second_answer_choice,
            "switch": self.first_answer_choice != self.second_answer_choice,
            "rationale_algorithm": {
                "name": self.question.rationale_selection_algorithm,
                "version": self.choose_rationales.version,
                "description": str(self.choose_rationales.description),
            },
            "rationales": [
                {"id": id, "text": rationale}
                for choice, label, rationales, texts in self.rationale_choices
                for id, rationale in rationales
                if id is not None
            ],
            "chosen_rationale_id": self.chosen_rationale_id,
            "success": "correct" if grade == 1.0 else "incorrect",
            "grade": grade,
        }
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
        Stick to my rationale is no longer saved as ShownRationale with an
        empty shown_answer
        """
        rationale_ids = [
            rationale[0]
            for _, _, rationales, _ in self.rationale_choices
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
        context = super().get_context_data(**kwargs)
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
        context = super().get_context_data(**kwargs)
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
        super().__init__(*args, **kwargs)

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
                f"to_{question.get_choice_label(i)}",
                f"To {question.get_choice_label(i)}",
            )
            for i in range(1, question.answerchoice_set.count() + 1)
        ]
        # Initialize a list of answers that we can add details to
        answers = []
        for i, answer in enumerate(question.answerchoice_set.all(), start=1):
            # Get the label for the row, and the counts for how many students
            # chose this answer the first time, and the second time.
            answer_row = {
                "label": f"Answer {question.get_choice_label(i)}: {answer.text}",
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
    if request.headers.get("Referer"):
        # We probably got here from within the LMS, and the user has
        # third-party cookies disabled, so we show help on enabling cookies for
        # this site.
        return render(
            request, "peerinst/cookie_help.html", {"host": request.get_host()}
        )
    return redirect_to_login(request.get_full_path())


def question(request, question_id, assignment_id=None):
    """
    Load common question data and dispatch to the right question stage. This
    dispatcher loads the session state and relevant database objects. Based on
    the available data, it delegates to the correct view class.
    """
    if not request.user.is_authenticated:
        return redirect_to_login_or_show_cookie_help(request)

    # Collect common objects required for the view
    assignment = get_object_or_none(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)

    # Reload question through proxy based on type, if needed
    if question.type == "RO":
        question = get_object_or_404(RationaleOnlyQuestion, pk=question_id)

    custom_key = (
        f"{str(assignment.pk) if assignment else 'test'}:{str(question.pk)}"
    )
    stage_data = SessionStageData(request.session, custom_key)
    user_token = request.user.username
    view_data = {
        "request": request,
        "assignment": assignment,
        "question": question,
        "user_token": user_token,
        "answer_choices": question.get_choices_with_correct(),
        "custom_key": custom_key,
        "stage_data": stage_data,
        "answer": models.Answer.objects.filter(
            assignment=assignment,
            question=question,
            user_token=user_token,
        ).last(),
    }

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
        stage_class = QuestionStartView

    logger_auth.info(
        f"Access type {request.session.get('access_type')} for {user_token} to assignment {assignment} and question {question} dispatched to {stage_class}"  # noqa
    )
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
def reset_question(request, question_id, assignment_id=None):
    """Clear all answers from user (for testing)"""
    assignment = get_object_or_none(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)
    user_token = request.user.username
    answer = get_object_or_none(
        models.Answer,
        assignment=assignment,
        question=question,
        user_token=user_token,
    )
    if answer:
        answer.delete()

    if assignment:
        return HttpResponseRedirect(
            reverse(
                "question",
                kwargs={
                    "assignment_id": assignment.pk,
                    "question_id": question.pk,
                },
            )
        )
    return HttpResponseRedirect(
        reverse(
            "question-test",
            kwargs={
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
                    return super().dispatch(*args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backup_avatar = os.path.join(
            settings.STATIC_URL, "components/img/logo.gif"
        )
        try:
            if self.request.user.saltisemember.picture:
                context["avatar"] = self.request.user.saltisemember.picture.url
            else:
                context["avatar"] = backup_avatar
        except SaltiseMember.DoesNotExist:
            context["avatar"] = backup_avatar
        return context


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
        context = super().get_context_data(**kwargs)
        context["teacher"] = self.teacher

        return context


class TeacherDetailView(TeacherBase, DetailView):
    """Teacher account"""

    model = Teacher
    template_name = "peerinst/teacher/details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # provides collection data to collection foldable
        context["owned_collections"] = Collection.objects.filter(
            owner=self.request.user.teacher
        )
        context["LTI_key"] = str(settings.LTI_BASIC_CLIENT_KEY)
        context["LTI_secret"] = str(settings.LTI_BASIC_CLIENT_SECRET)
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

        # Exclude assignments with less than 5 student answers per question
        # on average
        return (
            Assignment.objects.exclude(
                identifier__in=self.teacher.assignments.all()
            )
            .values("pk", "title")
            .annotate(
                n_answers=Subquery(
                    Answer.objects.filter(assignment=OuterRef("pk"))
                    .values("assignment")
                    .annotate(count=Count("pk"))
                    .values("count")[:1],
                    output_field=IntegerField(),
                )
            )
            .annotate(
                n_questions=Subquery(
                    AssignmentQuestions.objects.filter(
                        assignment=OuterRef("identifier")
                    )
                    .values("assignment")
                    .annotate(count=Count("pk"))
                    .values("count")[:1],
                    output_field=IntegerField(),
                )
            )
            .annotate(a_per_q=F("n_answers") / F("n_questions"))
            .exclude(a_per_q__lt=5)
            .order_by("title")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teacher"] = self.teacher
        context["form"] = forms.TeacherAssignmentsForm()

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
        context = super().get_context_data(**kwargs)
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
                return HttpResponseRedirect(
                    reverse(
                        "group-details",
                        kwargs={"group_hash": form.instance.hash},
                    )
                )
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
    return pre_filtered_list.filter(
        Q(title__icontains=search_string)
        | Q(description__icontains=search_string)
    )


# AJAX functions
@ajax_login_required
@ajax_user_passes_test(lambda u: hasattr(u, "teacher"))
def assignment_search_beta(request):
    FILTERS = [
        "category__title",
        "discipline.title",
        "difficulty.label",
        "peer_impact.label",
    ]

    if search_string := request.GET.get("search_string", default=""):
        start = time.perf_counter()

        terms = search_string.split()
        query = [t for t in terms if t.split("::")[0].lower() not in FILTERS]

        # Search
        s = as_ES(" ".join(query))

        # Serialize
        results = [hit.to_dict() for hit in s[:50]]

        meta = {
            "hit_count": s.count() if results else 0,
        }

        search_logger.info(
            f"Assignment search: {time.perf_counter() - start:.2e}s - {search_string}"
        )

        return JsonResponse({"results": results, "meta": meta}, safe=False)

    return JsonResponse({})


@ajax_login_required
@ajax_user_passes_test(lambda u: hasattr(u, "teacher"))
def collection_search_beta(request):
    FILTERS = [
        "category__title",
        "discipline.title",
        "difficulty.label",
        "peer_impact.label",
    ]

    if search_string := request.GET.get("search_string", default=""):
        start = time.perf_counter()

        terms = search_string.split()
        query = [t for t in terms if t.split("::")[0].lower() not in FILTERS]

        # Search
        s = cs_ES(" ".join(query))

        # Serialize
        results = [hit.to_dict() for hit in s[:50]]

        meta = {
            "hit_count": s.count() if results else 0,
        }

        search_logger.info(
            f"Collection search: {time.perf_counter() - start:.2e}s - {search_string}"
        )

        return JsonResponse({"results": results, "meta": meta}, safe=False)

    return JsonResponse({})


@ajax_login_required
@ajax_user_passes_test(lambda u: hasattr(u, "teacher"))
def question_search_beta(request, page=0):
    FILTERS = [
        "category__title",
        "discipline.title",
        "difficulty.label",
        "peer_impact.label",
    ]
    PAGINATION_LIMIT = 10

    search_string = request.GET.get("search_string", default="")

    if search_string:
        start = time.perf_counter()
        # Parse to remove filter terms from search string
        filters = []
        terms = search_string.split()
        query = []
        for t in terms:
            if t.split("::")[0].lower() in FILTERS:
                filters.append(
                    (
                        f"{t.split('::')[0]}".lower(),
                        t.split("::")[1].replace("_", " ").lower(),
                    )
                )
            else:
                query.append(t)

        # Question flags need to be real time, not from index
        flagged = list(Question.flagged_objects.values_list("id", flat=True))
        # Search
        s = qs_ES(" ".join(query), filters, flagged)
        # Serialize
        if page < 0:
            page = 0
        if page > s.count() // PAGINATION_LIMIT:
            page = s.count() // PAGINATION_LIMIT
        start_index = page * PAGINATION_LIMIT
        end_index = (page + 1) * PAGINATION_LIMIT
        results = [hit.to_dict() for hit in s[start_index:end_index]]
        # Add metadata
        if results:
            _c = []
            for c in (
                x["category"] if "category" in x else [] for x in results
            ):
                for a in c:
                    _c.append(a["title"])
            categories = sorted(set(_c))
            difficulties = sorted({r["difficulty"]["label"] for r in results})
            disciplines = sorted({r["discipline"]["title"] for r in results})
            impacts = sorted({r["peer_impact"]["label"] for r in results})
            meta = {
                "categories": categories,
                "difficulties": [
                    (d, _d[1])
                    for _d in Question.DIFFICULTY_LABELS
                    for d in difficulties
                    if _d[0] == d
                ],
                "disciplines": disciplines,
                "impacts": [
                    (i, _i[1])
                    for _i in Question.PEER_IMPACT_LABELS
                    for i in impacts
                    if _i[0] == i
                ],
                "hit_count": s.count(),
                "page": page,
                "page_size": PAGINATION_LIMIT,
            }
        else:
            meta = {
                "categories": [],
                "difficulties": [],
                "disciplines": [],
                "impacts": [],
                "hit_count": 0,
                "page": 0,
                "page_size": PAGINATION_LIMIT,
            }

        search_logger.info(
            f"Question search: {time.perf_counter() - start:.2e}s - {search_string}"
        )

        return JsonResponse({"results": results, "meta": meta}, safe=False)

    return JsonResponse({})


def question_search(request):
    start = time.perf_counter()

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
                term, search_list, (type == "assignment")
            )
            query_term = query_term.exclude(id__in=q_qs).distinct()

            query_term = [
                q
                for q in query_term
                if q not in query_all
                and q.is_not_flagged
                and q.is_not_missing_answer_choices
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

        end = time.perf_counter()

        performance_logger.info(
            f"ORM time to query '{search_string}': {end - start:E}s"
        )
        performance_logger.info(f"Hit count: {len(query_all)}")

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

    # Ensure only groups belonging to teacher are retained, if empty redirect
    student_groups = teacher.current_groups.filter(
        pk__in=student_groups
    ).values_list("pk")

    if len(student_groups) == 0:
        return HttpResponseRedirect(reverse("report_selector"))

    if request.GET.getlist("assignments"):
        assignment_list = request.GET.getlist("assignments")
    elif assignment_id:
        assignment_list = [urllib.parse.unquote(assignment_id)]
    else:
        assignment_list = teacher.assignments.all().values_list(
            "identifier", flat=True
        )

    group_school_id_needed = any(
        StudentGroup.objects.filter(pk__in=student_groups).values_list(
            "student_id_needed", flat=True
        )
    )

    assignment_data = report_data_by_assignment(
        assignment_list, student_groups, teacher, group_school_id_needed
    )

    context = {}
    context["data"] = assignment_data
    context["group_school_id_needed"] = group_school_id_needed
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
    teacher = get_object_or_404(Teacher, user=request.user)

    student_groups = request.GET.getlist("student_groups")
    assignment_list = request.GET.getlist("assignments")

    # Ensure only groups belonging to teacher are retained, if empty redirect
    student_groups = teacher.current_groups.filter(
        pk__in=student_groups
    ).values_list("pk")

    if len(student_groups) == 0:
        return JsonResponse({})

    j = []
    for a_str in assignment_list:
        a = Assignment.objects.get(identifier=a_str)
        d_a = {}
        d_a["assignment"] = a.identifier
        d_a["questions"] = []
        for q in a.questions.order_by("assignmentquestions__rank"):
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


# @login_required
# @user_passes_test(student_check, login_url="/access_denied_and_logout/")
# def connect_group_to_course(request):
#
#     course_pk = request.POST.get("course_pk")
#     student_group = StudentGroup.objects.get(pk=request.POST.get("group_pk"))
#
#     students_as_students = student_group.students.values_list(
#         "student", flat=True
#     )
#     students_as_users = User.objects.filter(pk__in=students_as_students)
#
#     clone = setup_link_to_group(course_pk, students_as_users)
#
#     date = clone.created_on.strftime("%b. %d, %Y, %I:%S %p")
#
#     return JsonResponse(
#         {
#             "action": "posted",
#             "linked_course_pk": clone.pk,
#             "linked_course_title": clone.title,
#             "linked_course_created_date": date,
#         }
#     )
#
#
# @login_required
# @user_passes_test(student_check, login_url="/access_denied_and_logout/")
# def disconnect_group_from_course(request):
#
#     course_pk = request.POST.get("course_pk")
#
#     try:
#         setup_unlink_from_group(course_pk)
#     except ValidationError:
#         return JsonResponse({"action": "error"})
#
#     return JsonResponse({"action": "posted"})
