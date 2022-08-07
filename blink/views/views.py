import contextlib
import random
from datetime import datetime

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormView

from blink import forms
from blink.models import (
    BlinkAnswer,
    BlinkAssignment,
    BlinkAssignmentQuestion,
    BlinkQuestion,
    BlinkRound,
)
from peerinst.mixins import LoginRequiredMixin
from peerinst.models import Teacher


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
                "blink/blink_error.html",
                context={
                    "message": "Assignment does not belong to this teacher",
                    "url": reverse("teacher", kwargs={"pk": teacher.pk}),
                },
            )

    except Exception:
        return TemplateResponse(
            request,
            "blink/blink_error.html",
            context={"message": "Error", "url": reverse("logout")},
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
                    "blink:blink-summary",
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
                "blink/blink_error.html",
                context={
                    "message": "Assignment does not belong to this teacher",
                    "url": reverse("teacher", kwargs={"pk": teacher.pk}),
                },
            )

    except Exception:
        return TemplateResponse(
            request,
            "blink/blink_error.html",
            context={"message": "Error", "url": reverse("logout")},
        )


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
                reverse("blink:blink-summary", kwargs={"pk": blinkquestion.pk})
            )
        else:
            return HttpResponseRedirect(
                reverse(
                    "blink:blink-question", kwargs={"pk": blinkquestion.pk}
                )
            )
    except Exception:
        # Else, redirect to summary for last active question latest_round =
        # BlinkRound.objects.filter(question__in=teacher.blinkquestion_set.all()).latest('activate_time')
        # return HttpResponseRedirect(reverse('blink-summary', kwargs={'pk' :
        # latest_round.question.pk})) Else, redirect to waiting room
        return HttpResponseRedirect(
            reverse(
                "blink:blink-waiting",
                kwargs={"username": teacher.user.username},
            )
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
        url = reverse("blink:blink-question", kwargs={"pk": blinkquestion.pk})
        return JsonResponse({"action": url})
    except Exception:
        if not teacher.blinkassignment_set.filter(active=True).exists():
            return JsonResponse({"action": "stop"})
        try:
            latest_round = BlinkRound.objects.filter(
                question__in=teacher.blinkquestion_set.all()
            ).latest("activate_time")
            url = reverse(
                "blink:blink-summary", kwargs={"pk": latest_round.question.pk}
            )
            return JsonResponse({"action": url})
        except Exception:
            return JsonResponse({"action": "stop"})


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
                        "blink:blink-summary",
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
                        "blink:blink-question",
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


def blink_latest_results(request, pk):

    results = {}

    blinkquestion = BlinkQuestion.objects.get(pk=pk)
    blinkround = BlinkRound.objects.filter(question=blinkquestion).latest(
        "deactivate_time"
    )

    c = 1
    for label, _text in blinkquestion.question.get_choices():
        results[label] = (
            BlinkAnswer.objects.filter(question=blinkquestion)
            .filter(voting_round=blinkround)
            .filter(answer_choice=c)
            .count()
        )
        c = c + 1

    return JsonResponse(results)


# This is a very temporary approach with minimum checking for permissions
@login_required
def blink_reset(request, pk):

    # blinkquestion = BlinkQuestion.objects.get(pk=pk)

    return HttpResponseRedirect(
        reverse("blink:blink-summary", kwargs={"pk": pk})
    )


@login_required
@require_POST
def blink_assignment_set_time(request, pk):

    form = forms.BlinkSetTimeForm(request.POST)
    blink_assignment = get_object_or_404(BlinkAssignment, key=pk)
    if form.is_valid():
        for blink_question in blink_assignment.blinkquestions.all():
            blink_question.time_limit = form.cleaned_data["time_limit"]
            blink_question.save()

    return HttpResponseRedirect(
        reverse("blink:blinkAssignment-start", kwargs={"pk": pk})
    )


def blink_status(request, pk):
    blinkquestion = BlinkQuestion.objects.get(pk=pk)

    response = {"status": blinkquestion.active}
    return JsonResponse(response)


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
        "blink/blink_waiting.html",
        context={
            "assignment": assignment,
            "teacher": teacher,
            "form": forms.BlinkSetTimeForm(),
        },
    )


class BlinkAssignmentCreate(LoginRequiredMixin, CreateView):

    model = BlinkAssignment
    fields = ["title"]
    template_name = "blink/blinkassignment_form.html"

    def form_valid(self, form):
        key = random.randrange(10000000, 99999999)
        while key in BlinkAssignment.objects.all():
            key = random.randrange(10000000, 99999999)
        form.instance.key = key
        form.instance.teacher = Teacher.objects.get(user=self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        if Teacher.objects.filter(user=self.request.user).exists():
            return reverse(
                "blink:blinkAssignment-update", kwargs={"pk": self.object.id}
            )
        else:
            return reverse("welcome")


class BlinkAssignmentUpdate(LoginRequiredMixin, DetailView):

    model = BlinkAssignment
    template_name = "blink/blinkassignment_detail.html"

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
                        "blink:blinkAssignment-update",
                        kwargs={"pk": self.object.pk},
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
                    except Exception as e:
                        print(e)
                        return HttpResponse("error")

                    return HttpResponseRedirect(
                        reverse(
                            "blink:blinkAssignment-update",
                            kwargs={"pk": self.object.pk},
                        )
                    )
                else:
                    print(forms.AddBlinkForm(request.POST))
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
                                "blink:blinkAssignment-update",
                                kwargs={"pk": self.object.pk},
                            )
                        )
                    else:
                        return HttpResponse("error")
        else:
            return HttpResponse("error3")


class BlinkQuestionDetailView(DetailView):

    model = BlinkQuestion
    template_name = "blink/blinkquestion_detail.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            with contextlib.suppress(Exception):
                r = BlinkRound.objects.get(
                    question=self.get_object(), deactivate_time__isnull=True
                )

                if not request.session.get(
                    f"BQid_{self.get_object().key}_R_{str(r.id)}", False
                ):
                    return HttpResponseRedirect(
                        reverse(
                            "blink:blink-question",
                            kwargs={"pk": self.get_object().pk},
                        )
                    )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
                int(self.request.session.get(f"BQid_{self.object.key}", 0))
            )

        context["teacher"] = self.object.teacher.user.username
        context["round"] = BlinkRound.objects.filter(
            question=self.object
        ).count()
        context["time_left"] = time_left

        return context


class BlinkQuestionFormView(SingleObjectMixin, FormView):

    form_class = forms.BlinkAnswerForm
    template_name = "blink/blink.html"
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
                "blink/blink_error.html",
                context={
                    "message": "Voting is closed",
                    "url": reverse(
                        "blink:blink-get-current",
                        kwargs={"username": self.object.teacher.user.username},
                    ),
                },
            )

        if self.request.session.get(
            "BQid_" + self.object.key + "_R_" + str(blinkround.id), False
        ):
            return TemplateResponse(
                self.request,
                "blink/blink_error.html",
                context={
                    "message": "You may only vote once",
                    "url": reverse(
                        "blink:blink-get-current",
                        kwargs={"username": self.object.teacher.user.username},
                    ),
                },
            )
        else:
            if self.object.active:
                try:
                    BlinkAnswer(
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
                        "blink/blink_error.html",
                        context={
                            "message": "Error; try voting again",
                            "url": reverse(
                                "blink:blink-get-current",
                                kwargs={
                                    "username": self.object.teacher.user.username  # noqa
                                },
                            ),
                        },
                    )
            else:
                return TemplateResponse(
                    self.request,
                    "blink/blink_error.html",
                    context={
                        "message": "Voting is closed",
                        "url": reverse(
                            "blink:blink-get-current",
                            kwargs={
                                "username": self.object.teacher.user.username
                            },
                        ),
                    },
                )

        return super().form_valid(form)

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super().get_form_kwargs()
        kwargs.update(answer_choices=self.object.question.get_choices())
        return kwargs

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["object"] = self.object

        return context

    def get_success_url(self):
        return reverse("blink:blink-summary", kwargs={"pk": self.object.pk})
