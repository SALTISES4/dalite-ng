# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
import logging
import random

import re
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import redirect_to_login
from django.core.mail import mail_admins, send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.template import loader
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.views.generic.list import ListView
from django_lti_tool_provider.signals import Signals
from django_lti_tool_provider.models import LtiUserData
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from . import heartbeat_checks
from . import forms
from . import models
from . import rationale_choice
from .util import SessionStageData, get_object_or_none, int_or_none, roundrobin
from .admin_views import get_question_rationale_aggregates

from .models import Student, StudentGroup, Teacher, Assignment, BlinkQuestion, BlinkAnswer, BlinkRound, BlinkAssignment, BlinkAssignmentQuestion, Question, Answer, Discipline, VerifiedDomain
from django.contrib.auth.models import User

#blink
from django.http import JsonResponse
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from django.contrib.sessions.models import Session

#reports
from django.db.models.expressions import Func
from django.db.models import Count

# tos
from tos.models import Consent


LOGGER = logging.getLogger(__name__)

# Views related to Auth



def landing_page(request):
    disciplines = {}

    disciplines[str('All')] = {}
    disciplines[str('All')][str('questions')] = Question.objects.count()
    disciplines[str('All')][str('rationales')] = Answer.objects.count()
    disciplines[str('All')][str('students')] = Student.objects.count()
    disciplines[str('All')][str('teachers')] = Teacher.objects.count()

    for d in Discipline.objects.annotate(num_q=Count('question')).order_by('-num_q')[:3]:
        disciplines[str(d.title)] = {}
        disciplines[str(d.title)][str('questions')] = Question.objects.filter(discipline=d).count()
        disciplines[str(d.title)][str('rationales')] = Answer.objects.filter(question__discipline=d).count()

        question_list=d.question_set.values_list('id',flat=True)
        disciplines[str(d.title)][str('students')] = \
        len(\
            set(\
                Answer.objects.filter(question_id__in=question_list)\
                .exclude(user_token='')\
                .values_list('user_token',flat=True)))

        disciplines[str(d.title)]['teachers'] = d.teacher_set.count()

    disciplines_json = json.dumps(disciplines)


    ### try again, with re-ordering
    disciplines_array = []

    d2 = {}
    d2[str('name')] = str('All')
    d2[str('questions')] = Question.objects.count()
    d2[str('rationales')] = Answer.objects.count()
    d2[str('students')] = Student.objects.count()
    d2[str('teachers')] = Teacher.objects.count()

    disciplines_array.append(d2)

    for d in Discipline.objects.annotate(num_q=Count('question')).order_by('-num_q')[:3]:
        d2 = {}
        d2[str('name')] = str(d.title)
        d2[str('questions')] = Question.objects.filter(discipline=d).count()
        d2[str('rationales')] = Answer.objects.filter(question__discipline=d).count()

        question_list=d.question_set.values_list('id',flat=True)
        disciplines[str(d.title)][str('students')] = \
        len(\
            set(\
                Answer.objects.filter(question_id__in=question_list)\
                .exclude(user_token='')\
                .values_list('user_token',flat=True)))

        d2[str('teachers')] = d.teacher_set.count()

        disciplines_array.append(d2)

    return TemplateResponse(
        request,
        'registration/landing_page.html',
        context={
            'disciplines': disciplines_array,
            'json': disciplines_json,
        })


def admin_check(user):
    return user.is_superuser


@login_required
@user_passes_test(admin_check,login_url='/welcome/',redirect_field_name=None)
def dashboard(request):

    html_email_template_name = 'registration/account_activated_html.html'

    if request.method=='POST':
        form = forms.ActivateForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            try:
                user.is_active = True
                user.save()

                if form.cleaned_data['is_teacher']:
                    teacher = Teacher(user=user)
                    teacher.save()
            except:
                pass

            # Notify user
            email_context = dict(
                username=user.username,
                site_name='myDALITE',
            )
            send_mail(
                _('Your myDALITE account has been activated'),
                'Dear {},\n\nYour account has been recently activated. \n\nYou can login at:\n\n{}\n\nCheers,\nThe myDalite Team'.format(user.username,'https://'+request.get_host(),),
                'noreply@myDALITE.org',
                [user.email],
                fail_silently=True,
                html_message=loader.render_to_string(html_email_template_name, context=email_context, request=request),
            )


    return TemplateResponse(
        request,
        'peerinst/dashboard.html',
        context={
            'new_users': User.objects.filter(is_active=False).order_by('-date_joined'),
        })


def sign_up(request):

    template = "registration/sign_up.html"
    html_email_template_name = "registration/sign_up_admin_email_html.html"
    context = {}

    if request.method == "POST":
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Set new users as inactive until verified by Administrator
                form.instance.is_active = False
                form.save()
                # Notify administrators
                try:
                    email_context = dict(
                        user=form.cleaned_data['username'],
                        date=timezone.now(),
                        email=form.cleaned_data['email'],
                        url=form.cleaned_data['url'],
                        site_name='myDALITE',
                    )
                    mail_admins(
                        'New user request',
                        'Dear administrator,\n\nA new user {} was created on {}. \n\nEmail: {}  \nVerification url: {} \n\nAccess your administrator account to activate this new user.\n\n{}\n\nCheers,\nThe myDalite Team'.format(form.cleaned_data['username'],timezone.now(),form.cleaned_data['email'],form.cleaned_data['url'],'https://'+request.get_host()+reverse('dashboard')),
                        fail_silently=True,
                        html_message=loader.render_to_string(html_email_template_name, context=email_context, request=request),
                    )
                except:
                    pass

                return TemplateResponse(request,'registration/sign_up_done.html')
            except:
                pass
        else:
            context['form'] = form
    else:
        context['form'] = forms.SignUpForm()

    return render(request,template,context)


def terms_teacher(request):
    return TemplateResponse(request, 'registration/terms.html')


def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect(reverse('landing_page'))


def welcome(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        return HttpResponseRedirect(reverse('teacher', kwargs={ 'pk' : teacher.pk }))
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('assignment-list'))


def access_denied(request):
    return HttpResponse('Access denied')


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


def student_check(user):
    try:
        if user.teacher:
            # Let through Teachers unconditionally
            return True
    except:
        try:
            if user.student:
                # Block Students
                return False
        except:
            # Allow through all non-Students, i.e. "guests"
            return True

class NoStudentsMixin(object):
    """A simple mixin to explicitly allow Teacher but prevent Student access to a view."""
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(NoStudentsMixin, cls).as_view(**initkwargs)
        return user_passes_test(student_check, login_url='/access_denied/')(view)


class AssignmentListView(NoStudentsMixin, LoginRequiredMixin, ListView):
    """List of assignments used for debugging purposes."""
    model = models.Assignment


class AssignmentUpdateView(NoStudentsMixin,LoginRequiredMixin,DetailView):
    """View for updating assignment."""

    model = Assignment

    def get_context_data(self, **kwargs):
        context = super(AssignmentUpdateView, self).get_context_data(**kwargs)
        context['teacher'] = Teacher.objects.get(user=self.request.user)

        return context

    def get_object(self):
        return get_object_or_404(models.Assignment, pk=self.kwargs['assignment_id'])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user.is_authenticated():
            form = forms.AddRemoveQuestionForm(request.POST)
            print(form)
            if form.is_valid():
                question = form.cleaned_data['q']
                if not question in self.object.questions.all():
                    self.object.questions.add(question)
                else:
                    self.object.questions.remove(question)
                self.object.save()

                return HttpResponseRedirect(reverse("assignment-update", kwargs={'assignment_id': self.object.pk}))
            else:
                return HttpResponse("error")
        else:
            return HttpResponse("error3")



class QuestionListView(NoStudentsMixin, LoginRequiredMixin, ListView):
    """List of questions used for debugging purposes."""
    model = models.Assignment

    def get_queryset(self):
        self.assignment = get_object_or_404(models.Assignment, pk=self.kwargs['assignment_id'])
        return self.assignment.questions.all()

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)
        context.update(assignment=self.assignment)
        return context


# Views related to Question

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
        return context

    def send_grade(self):
        if not self.lti_data:
            # We are running outside of an LTI context, so we don't need to send a grade.
            return
        if not self.lti_data.edx_lti_parameters.get('lis_outcome_service_url'):
            # edX didn't provide a callback URL for grading, so this is an unscored problem.
            return

        Signals.Grade.updated.send(
            __name__,
            user=self.request.user,
            custom_key=self.custom_key,
            grade=self.answer.get_grade(),
        )


class QuestionReload(Exception):
    """Raised to cause a reload of the page, usually to start over in case of an error."""


class QuestionFormView(QuestionMixin, FormView):
    """Base class for the form views in the student UI."""

    def emit_event(self, name, **data):
        """Log an event in a JSON format similar to the edx-platform tracking logs.
        """
        if not self.lti_data:
            # Only log when running within an LTI context.
            return

        # Extract information from LTI parameters.
        course_id = self.lti_data.edx_lti_parameters.get('context_id')

        try:
            edx_org = CourseKey.from_string(course_id).org
        except InvalidKeyError:
            # The course_id is not from edX. Don't place the org in the logs.
            edx_org = None

        grade_handler_re = re.compile(
            'https?://[^/]+/courses/{course_id}/xblock/(?P<usage_key>[^/]+)/'.format(
                course_id=re.escape(course_id)
            )
        )
        usage_key = None
        outcome_service_url = self.lti_data.edx_lti_parameters.get('lis_outcome_service_url')
        if outcome_service_url:
            usage_key = grade_handler_re.match(outcome_service_url)
            if usage_key:
                usage_key = usage_key.group('usage_key')
            # Grading is enabled, so include information about max grade in event data
            data['max_grade'] = 1.0
        else:
            # Grading is not enabled, so remove information about grade from event data
            if 'grade' in data:
                del data['grade']

        # Add common fields to event data
        data.update(
            assignment_id=self.assignment.pk,
            assignment_title=self.assignment.title,
            problem=usage_key,
            question_id=self.question.pk,
            question_text=self.question.text,
        )

        # Build event dictionary.
        META = self.request.META
        event = dict(
            accept_language=META.get('HTTP_ACCEPT_LANGUAGE'),
            agent=META.get('HTTP_USER_AGENT'),
            context=dict(
                course_id=course_id,
                module=dict(
                    usage_key=usage_key,
                ),
                username=self.user_token,
            ),
            course_id=course_id,
            event=data,
            event_source='server',
            event_type=name,
            host=META.get('SERVER_NAME'),
            ip=META.get('HTTP_X_REAL_IP', META.get('REMOTE_ADDR')),
            referer=META.get('HTTP_REFERER'),
            time=datetime.datetime.now().isoformat(),
            username=self.user_token,
        )

        if edx_org is not None:
            event['context']['org_id'] = edx_org

        # Write JSON to log file
        LOGGER.info(json.dumps(event))

        # Automatically keep track of student, student groups and their relationships based on lti data
        user = User.objects.get(username=self.user_token)
        student, created_student = Student.objects.get_or_create(student=user)
        group, created_group = StudentGroup.objects.get_or_create(name=course_id)
        if created_group:
            group.save()
        student.groups.add(group)
        student.save()

    def submission_error(self):
        messages.error(self.request, format_html(
            '<h3 class="messages-title">{}</h3>{}',
            _("There was a problem with your submission"),
            _('Check the form below.')))

    def form_invalid(self, form):
        self.submission_error()
        return super(QuestionFormView, self).form_invalid(form)

    def get_success_url(self):
        # We always redirect to the same HTTP endpoint.  The actual view is selected based on the
        # session state.
        return self.request.path

    def start_over(self, msg=None):
        """Start over with the current question.

        This redirect is used when inconsistent data is encountered and shouldn't be called under
        normal circumstances.
        """
        if msg is not None:
            messages.error(self.request, msg)
        raise QuestionReload()


class QuestionStartView(QuestionFormView):
    """Render a question with answer choices.

    The user can choose one answer and enter a rationale.
    """

    template_name = 'peerinst/question_start.html'
    form_class = forms.FirstAnswerForm

    def get_form_kwargs(self):
        kwargs = super(QuestionStartView, self).get_form_kwargs()
        kwargs.update(answer_choices=self.answer_choices)
        if self.request.method == 'GET':
            # Log when the page is first shown, mainly for the timestamp.
            self.emit_event('problem_show')
        return kwargs

    def form_valid(self, form):
        first_answer_choice = int(form.cleaned_data['first_answer_choice'])
        correct = self.question.is_correct(first_answer_choice)
        rationale = form.cleaned_data['rationale']
        self.stage_data.update(
            first_answer_choice=first_answer_choice,
            rationale=rationale,
            completed_stage='start',
        )
        self.emit_event(
            'problem_check',
            first_answer_choice=first_answer_choice,
            success='correct' if correct else 'incorrect',
            rationale=rationale,
        )
        return super(QuestionStartView, self).form_valid(form)


class QuestionReviewBaseView(QuestionFormView):
    """Common base class for sequential and non-sequential review types."""

    def determine_rationale_choices(self):
        if not hasattr(self, 'choose_rationales'):
            self.choose_rationales = rationale_choice.algorithms[
                self.question.rationale_selection_algorithm
            ]
        self.rationale_choices = self.stage_data.get('rationale_choices')
        if self.rationale_choices is not None:
            # The rationales we stored in the session have already been HTML-escaped – mark them as
            # safe to avoid double-escaping
            self.mark_rationales_safe(escape_html=False)
            return
        # Make the choice of rationales deterministic, so rationales won't change when reloading
        # the page after clearing the session.
        rng = random.Random((self.user_token, self.assignment.pk, self.question.pk))
        try:
            self.rationale_choices = self.choose_rationales(
                rng, self.first_answer_choice, self.rationale, self.question
            )
        except rationale_choice.RationaleSelectionError as e:
            self.start_over(e.message)
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
        usernames = models.FakeUsername.objects.values_list('name', flat=True)
        countries = models.FakeCountry.objects.values_list('name', flat=True)
        if not usernames or not countries:
            # No usernames or no countries were supplied, so we silently refrain from adding fake
            # attributions.  We need to ensure, though, that the rationales get properly escaped.
            self.mark_rationales_safe(escape_html=True)
            return
        fake_attributions = {}
        for choice, label, rationales in self.rationale_choices:
            attributed_rationales = []
            for id, text in rationales:
                if id is None:
                    # This is the "I stick with my own rationale" option.  Don't add a fake
                    # attribution, it might blow our cover.
                    attributed_rationales.append((id, text))
                    continue
                attribution = rng.choice(usernames), rng.choice(countries)
                fake_attributions[id] = attribution
                formatted_rationale = format_html('<q>{}</q> ({}, {})', text, *attribution)
                attributed_rationales.append((id, formatted_rationale))
            rationales[:] = attributed_rationales
        self.stage_data.update(fake_attributions=fake_attributions)

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewBaseView, self).get_form_kwargs()
        self.first_answer_choice = self.stage_data.get('first_answer_choice')
        self.rationale = self.stage_data.get('rationale')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionReviewBaseView, self).get_context_data(**kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.first_answer_choice),
            rationale=self.rationale,
            sequential_review=self.stage_data.get('completed_stage') == 'sequential-review',
        )
        return context


class QuestionSequentialReviewView(QuestionReviewBaseView):

    template_name = 'peerinst/question_sequential_review.html'
    form_class = forms.SequentialReviewForm

    def select_next_rationale(self):
        rationale_sequence = self.stage_data.get('rationale_sequence')
        if rationale_sequence:
            # We already have selected the rationales – just take the next one.
            self.current_rationale = rationale_sequence[self.stage_data.get('rationale_index')]
            self.current_rationale[2] = mark_safe(self.current_rationale[2])
            return
        self.choose_rationales = rationale_choice.simple_sequential
        self.determine_rationale_choices()
        # Select alternating rationales from the lists of rationales for the different answer
        # choices.  Skip the "I stick with my own rationale" option marked by id == None.
        rationale_sequence = list(roundrobin(
            [(id, label, rationale) for id, rationale in rationales if id is not None]
            for choice, label, rationales in self.rationale_choices
        ))
        self.current_rationale = rationale_sequence[0]
        self.stage_data.update(
            rationale_sequence=rationale_sequence,
            rationale_votes={},
            rationale_index=0,
        )

    def get_context_data(self, **kwargs):
        context = super(QuestionSequentialReviewView, self).get_context_data(**kwargs)
        self.select_next_rationale()
        context.update(
            current_rationale=self.current_rationale,
        )
        return context

    def form_valid(self, form):
        rationale_sequence = self.stage_data.get('rationale_sequence')
        rationale_votes = self.stage_data.get('rationale_votes')
        rationale_index = self.stage_data.get('rationale_index')
        current_rationale = rationale_sequence[rationale_index]
        rationale_votes[current_rationale[0]] = form.cleaned_data['vote']
        rationale_index += 1
        self.stage_data.update(
            rationale_index=rationale_index,
            rationale_votes=rationale_votes,
        )
        if rationale_index == len(rationale_sequence):
            # We've shown all rationales – mark the stage as finished.
            self.stage_data.update(completed_stage='sequential-review')
        return super(QuestionSequentialReviewView, self).form_valid(form)


class QuestionReviewView(QuestionReviewBaseView):
    """The standard version of the review, showing all alternative rationales simultaneously."""

    template_name = 'peerinst/question_review.html'
    form_class = forms.ReviewAnswerForm

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewView, self).get_form_kwargs()
        self.determine_rationale_choices()
        kwargs.update(
            rationale_choices=self.rationale_choices,
        )
        return kwargs

    def form_valid(self, form):
        self.second_answer_choice = int(form.cleaned_data['second_answer_choice'])
        self.chosen_rationale_id = int_or_none(form.cleaned_data['chosen_rationale_id'])
        self.save_answer()
        self.emit_check_events()
        self.save_votes()
        self.stage_data.clear()
        self.send_grade()
        return super(QuestionReviewView, self).form_valid(form)

    def emit_check_events(self):
        grade = self.answer.get_grade()
        event_data = dict(
            second_answer_choice=self.second_answer_choice,
            switch=self.first_answer_choice != self.second_answer_choice,
            rationale_algorithm=dict(
                name=self.question.rationale_selection_algorithm,
                version=self.choose_rationales.version,
                description=unicode(self.choose_rationales.description),
            ),
            rationales=[
                {'id': id, 'text': rationale}
                for choice, label, rationales in self.rationale_choices
                for id, rationale in rationales
                if id is not None
            ],
            chosen_rationale_id=self.chosen_rationale_id,
            success='correct' if grade == 1.0 else 'incorrect',
            grade=grade,
        )
        self.emit_event('problem_check', **event_data)
        self.emit_event('save_problem_success', **event_data)

    def save_answer(self):
        """Validate and save the answer defined by the arguments to the database."""
        if self.chosen_rationale_id is not None:
            try:
                chosen_rationale = models.Answer.objects.get(id=self.chosen_rationale_id)
            except models.Answer.DoesNotExist:
                # Raises exception.
                self.start_over(_(
                    'The rationale you chose does not exist anymore.  '
                    'This should not happen.  Please start over with the question.'
                ))
            if chosen_rationale.first_answer_choice != self.second_answer_choice:
                self.start_over(_(
                    'The rationale you chose does not match your second answer choice.  '
                    'This should not happen.  Please start over with the question.'
                ))
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
            time=datetime.datetime.now().isoformat()
        )
        self.answer.save()
        if chosen_rationale is not None:
            self.record_fake_attribution_vote(chosen_rationale, models.AnswerVote.FINAL_CHOICE)

    def save_votes(self):
        rationale_votes = self.stage_data.get('rationale_votes')
        if rationale_votes is None:
            return
        for rationale_id, vote in rationale_votes.iteritems():
            try:
                rationale = models.Answer.objects.get(id=rationale_id)
            except models.Answer.DoesNotExist:
                # This corner case can only happen if an answer was deleted while the student was
                # answering the question.  Simply ignore these votes.
                continue
            if vote == 'up':
                rationale.upvotes += 1
                self.record_fake_attribution_vote(rationale, models.AnswerVote.UPVOTE)
            elif vote == 'down':
                rationale.downvotes += 1
                self.record_fake_attribution_vote(rationale, models.AnswerVote.DOWNVOTE)
            rationale.save()

    def record_fake_attribution_vote(self, answer, vote_type):
        fake_attributions = self.stage_data.get('fake_attributions')
        if fake_attributions is None:
            return
        fake_username, fake_country = fake_attributions[unicode(answer.id)]
        models.AnswerVote(
            answer=answer,
            assignment=self.assignment,
            user_token=self.user_token,
            fake_username=fake_username,
            fake_country=fake_country,
            vote_type=vote_type,
        ).save()


class QuestionSummaryView(QuestionMixin, TemplateView):
    """Show a summary of answers to the student and submit the data to the database."""

    template_name = 'peerinst/question_summary.html'

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


class HeartBeatUrl(View):

    def get(self, request):

        checks = []

        checks.append(heartbeat_checks.check_db_query())
        checks.append(heartbeat_checks.check_staticfiles())
        checks.extend(heartbeat_checks.test_global_free_percentage(
            settings.HEARTBEAT_REQUIRED_FREE_SPACE_PERCENTAGE))

        checks_ok = all((check.is_ok for check in checks))

        status = 200 if checks_ok else 500

        return TemplateResponse(
            request, "peerinst/heartbeat.html", context={"checks": checks},
            status=status)


class AnswerSummaryChartView(View):
    """
    This view draws a chart showing analytics about the answers
    that students chose for a question, and the rationales
    that they selected to back up those answers.
    """
    def __init__(self, *args, **kwargs):
        """
        Save the initialization arguments for later use
        """
        self.kwargs = kwargs
        super(AnswerSummaryChartView, self).__init__(*args, **kwargs)

    def get(self, request):
        """
        This method handles creation of a piece of context that can
        be used to draw the chart mentioned in the class docstring.
        """
        # Get the relevant assignment/question pairing
        question = self.kwargs.get('question')
        assignment = self.kwargs.get('assignment')
        # There are three columns that every chart will have - prefill them here
        static_columns = [
            ("label", "Choice",),
            ("before", "Before",),
            ("after", "After",),
        ]
        # Other columns will be dynamically present, depending on which choices
        # were available on a given question.
        to_columns = [
            (
                "to_{}".format(question.get_choice_label(i)),
                "To {}".format(question.get_choice_label(i)),
            ) for i in range(1, question.answerchoice_set.count()+1)
        ]
        # Initialize a list of answers that we can add details to
        answers = []
        for i, answer in enumerate(question.answerchoice_set.all(), start=1):
            # Get the label for the row, and the counts for how many students chose
            # this answer the first time, and the second time.
            answer_row = {
                "label": "Answer {}: {}".format(question.get_choice_label(i), answer.text),
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
                # For every other answer, determine the count of students who chose
                # this answer the first time, but the other answer the second time.
                answer_row[column[0]] = models.Answer.objects.filter(
                    question=question,
                    first_answer_choice=i,
                    second_answer_choice=j,
                    assignment=assignment,
                ).count()
            # Get the top five rationales for this answer to display underneath the chart
            _, rationales = get_question_rationale_aggregates(
                assignment,
                question,
                5,
                choice_id=i,
                include_own_rationales=True,
            )
            answer_row['rationales'] = rationales['chosen']
            # Save everything about this answer into the list of table rows
            answers.append(answer_row)
        # Build a list of all the columns that will be used in this chart
        columns = [
            {
                "name": name,
                "label": label,
            } for name, label in static_columns + to_columns
        ]
        # Build a two-dimensional list with a value for each cell in the chart
        answer_rows = [[row[column['name']] for column in columns] for row in answers]
        # Transform the rationales we got from the other function into a format we can easily
        # draw in the page using a template
        answer_rationales = [
            {
                'label': each['label'],
                'rationales': [
                    {
                        "text": rationale['rationale'].rationale,
                        "count": rationale['count'],
                    } for rationale in each['rationales'] if rationale['rationale'] is not None
                ]
            } for each in answers
        ]
        # Render the template using the relevant variables and return it as an HTTP response.
        return TemplateResponse(
            request,
            'peerinst/question_answers_summary.html',
            context={
                'question': question,
                'columns': columns,
                'answer_rows': answer_rows,
                'answer_rationales': answer_rationales
            }
        )


def redirect_to_login_or_show_cookie_help(request):
    """Redirect to login page outside of an iframe, show help on enabling cookies inside an iframe.

    We consider the request to come from within an iframe if the HTTP Referer header is set.  This
    isn't entirely accurate, but should be good enough.
    """
    if request.META.get('HTTP_REFERER'):
        # We probably got here from within the LMS, and the user has third-party cookies disabled,
        # so we show help on enabling cookies for this site.
        return render_to_response('peerinst/cookie_help.html', dict(host=request.get_host()))
    return redirect_to_login(request.get_full_path())


def question(request, assignment_id, question_id):
    """Load common question data and dispatch to the right question stage.

    This dispatcher loads the session state and relevant database objects.  Based on the available
    data, it delegates to the correct view class.
    """
    if not request.user.is_authenticated():
        return redirect_to_login_or_show_cookie_help(request)

    # Collect common objects required for the view
    assignment = get_object_or_404(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)
    custom_key = unicode(assignment.pk) + ':' + unicode(question.pk)
    stage_data = SessionStageData(request.session, custom_key)
    user_token = request.user.username
    view_data = dict(
        request=request,
        assignment=assignment,
        question=question,
        user_token=user_token,
        answer_choices=question.get_choices(),
        custom_key=custom_key,
        stage_data=stage_data,
        lti_data=get_object_or_none(LtiUserData, user=request.user, custom_key=custom_key),
        answer=get_object_or_none(
            models.Answer, assignment=assignment, question=question, user_token=user_token
        )
    )

    # Determine stage and view class

    if request.GET.get('show_results_view') == 'true':
        stage_class = AnswerSummaryChartView
    elif view_data['answer'] is not None:
        stage_class = QuestionSummaryView
    elif stage_data.get('completed_stage') == 'start':
        if question.sequential_review:
            stage_class = QuestionSequentialReviewView
        else:
            stage_class = QuestionReviewView
    elif stage_data.get('completed_stage') == 'sequential-review':
        stage_class = QuestionReviewView
    else:
        stage_class = QuestionStartView

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


def reset_question(request, assignment_id, question_id):
    """ Clear all answers from user (for testing) """

    assignment = get_object_or_404(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)
    user_token = request.user.username
    answer=get_object_or_none(
        models.Answer, assignment=assignment, question=question, user_token=user_token
    )
    answer.delete()

    return HttpResponseRedirect(reverse('question', kwargs={'assignment_id' : assignment.pk, 'question_id' : question.pk}))


# Views related to Teacher

class TeacherBase(LoginRequiredMixin,View):
    """Base view for Teacher for custom authentication"""

    def dispatch(self, *args, **kwargs):
        if self.request.user == Teacher.objects.get(pk=kwargs['pk']).user:
            if Consent.get(self.request.user.username, "teacher") is None:
                return HttpResponseRedirect(reverse("tos:modify", args=("teacher",)) + "?next=" + reverse("teacher", args=(kwargs["pk"],)))
            return super(TeacherBase, self).dispatch(*args, **kwargs)
        else:
            return HttpResponse('Access denied!')


class TeacherDetailView(TeacherBase,DetailView):

    model = Teacher

    def get_context_data(self, **kwargs):
        context = super(TeacherDetailView,self).get_context_data(**kwargs)
        context['LTI_key'] = str(settings.LTI_CLIENT_KEY)
        context['LTI_secret'] = str(settings.LTI_CLIENT_SECRET)
        context['LTI_launch_url'] = str('https://'+self.request.get_host()+'/lti/')
        context['tos_accepted'] = bool(Consent.get(self.get_object().user.username, "teacher"))

        # Set all blink assignments, questions, and rounds for this teacher to inactive
        for a in self.get_object().blinkassignment_set.all():
            if a.active:
                a.active = False
                a.save()

        for b in self.get_object().blinkquestion_set.all():
            if b.active:
                b.active = False
                b.save()

                open_rounds = BlinkRound.objects.filter(question=b).filter(deactivate_time__isnull=True)

                for open_round in open_rounds:
                    open_round.deactivate_time = timezone.now()
                    open_round.save()

        return context


class TeacherUpdate(TeacherBase,UpdateView):

    model = Teacher
    fields = ['institutions','disciplines']


class TeacherAssignments(TeacherBase,ListView):
    """View to modify assignments associated to Teacher"""

    model = Teacher
    template_name = 'peerinst/teacher_assignments.html'

    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        return Assignment.objects.all()

    def get_context_data(self, **kwargs):
        context = super(TeacherAssignments, self).get_context_data(**kwargs)
        context['teacher'] = self.teacher
        context['form'] = forms.AssignmentCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        form = forms.TeacherAssignmentsForm(request.POST)
        if form.is_valid():
            assignment = form .cleaned_data['assignment']
            if assignment in self.teacher.assignments.all():
                self.teacher.assignments.remove(assignment)
            else:
                self.teacher.assignments.add(assignment)
            self.teacher.save()
        else:
            form  = forms.AssignmentCreateForm(request.POST)
            if form.is_valid():
                assignment = Assignment(
                    identifier=form .cleaned_data['identifier'],
                    title=form .cleaned_data['title'],
                )
                assignment.save()
                self.teacher.assignments.add(assignment)
                self.teacher.save()
            else:
                return render(request, self.template_name, {'teacher': self.teacher,'form': form, 'object_list':Assignment.objects.all()})

        return HttpResponseRedirect(reverse('teacher-assignments',  kwargs={ 'pk' : self.teacher.pk }))


class TeacherGroups(TeacherBase,ListView):
    """View to modify groups associated to Teacher"""

    model = Teacher
    template_name = 'peerinst/teacher_groups.html'

    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        return StudentGroup.objects.all()

    def get_context_data(self, **kwargs):
        context = super(TeacherGroups, self).get_context_data(**kwargs)
        context['teacher'] = self.teacher
        context['form'] = forms.TeacherGroupsForm()

        return context

    def post(self, request, *args, **kwargs):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        form = forms.TeacherGroupsForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data['group']
            if group in self.teacher.groups.all():
                self.teacher.groups.remove(group)
            else:
                self.teacher.groups.add(group)
            self.teacher.save()

        return HttpResponseRedirect(reverse('teacher-groups',  kwargs={ 'pk' : self.teacher.pk }))


class TeacherBlinks(TeacherBase,ListView):
    """OBSOLETE??"""

    model = Teacher
    template_name = 'peerinst/teacher_blinks.html'

    def get_queryset(self):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        return BlinkQuestion.objects.all() # I don't think this is ever used

    def get_context_data(self, **kwargs):
        context = super(TeacherBlinks, self).get_context_data(**kwargs)
        context['teacher'] = self.teacher

        teacher_discipline_questions=Question.objects.filter(discipline__in=self.teacher.disciplines.all())

        teacher_blink_questions = [bk.question for bk in self.teacher.blinkquestion_set.all()]
        # Send as context questions not already part of teacher's blinks
        context['suggested_questions']=[q for q in teacher_discipline_questions if q not in teacher_blink_questions]

        return context

    def post(self, request, *args, **kwargs):
        self.teacher = get_object_or_404(Teacher, user=self.request.user)
        if request.POST.get('blink',False):
            form = forms.TeacherBlinksForm(request.POST)
            if form.is_valid():
                blink = form.cleaned_data["blink"]
                blink.current = (not blink.current)
                blink.save()

        if request.POST.get('new_blink',False):
            form = forms.CreateBlinkForm(request.POST)
            if form.is_valid():
                key = random.randrange(10000000,99999999)
                while key in BlinkQuestion.objects.all():
                    key = random.randrange(10000000,99999999)
                try:
                    blink = BlinkQuestion(
                        question=form.cleaned_data['new_blink'],
                        teacher=self.teacher,
                        time_limit=60,
                        key=key,
                    )
                    blink.save()
                except:
                    return HttpResponse("error")

        return HttpResponseRedirect(reverse('teacher-blinks',  kwargs={ 'pk' : self.teacher.pk }))

# Views related to Blink

class BlinkQuestionFormView(SingleObjectMixin,FormView):

    form_class = forms.BlinkAnswerForm
    template_name = 'peerinst/blink.html'
    model = BlinkQuestion

    def form_valid(self,form):
        self.object = self.get_object()

        try:
            blinkround=BlinkRound.objects.get(question=self.object,deactivate_time__isnull=True)
        except:
            return TemplateResponse(
                self.request,
                'peerinst/blink_error.html',
                context={
                    'message':"Voting is closed",
                    'url':reverse('blink-get-current', kwargs={'username': self.object.teacher.user.username})
                    })

        if self.request.session.get('BQid_'+self.object.key+'_R_'+str(blinkround.id), False):
            return TemplateResponse(
                self.request,
                'peerinst/blink_error.html',
                context={
                    'message':"You may only vote once",
                    'url':reverse('blink-get-current', kwargs={'username': self.object.teacher.user.username})
                    })
        else:
            if self.object.active:
                try:
                    models.BlinkAnswer(
                        question=self.object,
                        answer_choice=form.cleaned_data['first_answer_choice'],
                        vote_time=timezone.now(),
                        voting_round=blinkround,
                    ).save()
                    self.request.session['BQid_'+self.object.key+'_R_'+str(blinkround.id)] = True
                    self.request.session['BQid_'+self.object.key] = form.cleaned_data['first_answer_choice']
                except:
                    return TemplateResponse(
                        self.request,
                        'peerinst/blink_error.html',
                        context={
                            'message':"Error; try voting again",
                            'url':reverse('blink-get-current', kwargs={'username': self.object.teacher.user.username})
                            })
            else:
                return TemplateResponse(
                    self.request,
                    'peerinst/blink_error.html',
                    context={
                        'message':"Voting is closed",
                        'url':reverse('blink-get-current', kwargs={'username': self.object.teacher.user.username})
                        })

        return super(BlinkQuestionFormView,self).form_valid(form)

    def get_form_kwargs(self):
        self.object = self.get_object()
        kwargs = super(BlinkQuestionFormView, self).get_form_kwargs()
        kwargs.update(
            answer_choices=self.object.question.get_choices(),
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BlinkQuestionFormView, self).get_context_data(**kwargs)
        context['object'] = self.object

        return context

    def get_success_url(self):
        return reverse('blink-summary', kwargs={'pk': self.object.pk})


class BlinkQuestionDetailView(DetailView):

    model = BlinkQuestion

    def get_context_data(self, **kwargs):
        context = super(BlinkQuestionDetailView, self).get_context_data(**kwargs)

        # Check if user is a Teacher
        if self.request.user.is_authenticated() and  Teacher.objects.filter(user__username=self.request.user).exists():

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
                open_rounds = BlinkRound.objects.filter(question=self.object).filter(deactivate_time__isnull=True)
                for open_round in open_rounds:
                    open_round.deactivate_time = timezone.now()
                    open_round.save()

                # Create round
                r = BlinkRound(
                    question=self.object,
                    activate_time=datetime.datetime.now()
                )
                r.save()
            else:
                HttpResponseRedirect(reverse('teacher', kwargs={'pk':teacher.pk}))
        else:
            # Get current round, if any
            try:
                r = BlinkRound.objects.get(question=self.object,deactivate_time__isnull=True)
                elapsed_time = (timezone.now()-r.activate_time).seconds
                time_left = max(self.object.time_limit - elapsed_time,0)
            except:
                time_left = 0

            # Get latest vote, if any
            context['latest_answer_choice'] = self.object.question.get_choice_label(int(self.request.session.get('BQid_'+self.object.key,0)))

        context['teacher'] = self.object.teacher.user.username
        context['round'] = BlinkRound.objects.filter(question=self.object).count()
        context['time_left'] = time_left

        return context


@login_required
def blink_assignment_start(request,pk):
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

            return HttpResponseRedirect(reverse('blink-summary', kwargs={'pk': blinkassignment.blinkquestions.order_by('blinkassignmentquestion__rank').first().pk} ))

        else:
            return TemplateResponse(
                request,
                'peerinst/blink_error.html',
                context={
                    'message':"Assignment does not belong to this teacher",
                    'url':reverse('teacher', kwargs={'pk':teacher.pk})
                    })

    except:
        return TemplateResponse(
            request,
            'peerinst/blink_error.html',
            context={
                'message':"Error",
                'url':reverse('logout')
                })


@login_required
def blink_assignment_delete(request,pk):
    """View to delete a blink script"""

    # Check this user is a Teacher and owns this assignment
    try:
        teacher = Teacher.objects.get(user__username=request.user)
        blinkassignment = BlinkAssignment.objects.get(key=pk)

        if blinkassignment.teacher == teacher:

            # Delete
            blinkassignment.delete()

            return HttpResponseRedirect(reverse('teacher', kwargs={'pk':teacher.pk}))

        else:
            return TemplateResponse(
                request,
                'peerinst/blink_error.html',
                context={
                    'message':"Assignment does not belong to this teacher",
                    'url':reverse('teacher', kwargs={'pk':teacher.pk})
                    })

    except:
        return TemplateResponse(
            request,
            'peerinst/blink_error.html',
            context={
                'message':"Error",
                'url':reverse('logout')
                })


def blink_get_next(request,pk):
    """View to process next question in a series of blink questions based on state."""

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
                user_role = Teacher.objects.get(user__username=request.user)
                print(blinkassignment.blinkassignmentquestion_set.all())
                return HttpResponseRedirect(reverse('blink-summary', kwargs={'pk': blinkassignment.blinkassignmentquestion_set.get(rank=rank+1).blinkquestion.pk} ))
            except:
                # Others to new question page
                return HttpResponseRedirect(reverse('blink-question', kwargs={'pk': blinkassignment.blinkassignmentquestion_set.get(rank=rank+1).blinkquestion.pk} ))

        else:
            blinkassignment.active = False
            blinkassignment.save()
            return HttpResponseRedirect(reverse('teacher', kwargs={'pk':teacher.pk}))

    except:
        return HttpResponse("Error")


def blink_get_current(request,username):
    """View to redirect user to latest active BlinkQuestion for teacher."""

    try:
        # Get teacher
        teacher = Teacher.objects.get(user__username=username)
    except:
        return HttpResponse("Teacher does not exist")

    try:
        # Redirect to current active blinkquestion, if any, if this user has not voted yet in this round
        blinkquestion = teacher.blinkquestion_set.get(active=True)
        blinkround = blinkquestion.blinkround_set.latest('activate_time')
        if request.session.get('BQid_'+blinkquestion.key+'_R_'+str(blinkround.id), False):
             return HttpResponseRedirect(reverse('blink-summary', kwargs={'pk' : blinkquestion.pk}))
        else:
            return HttpResponseRedirect(reverse('blink-question', kwargs={'pk' : blinkquestion.pk}))
    except:
        # Else, redirect to summary for last active question
        #latest_round = BlinkRound.objects.filter(question__in=teacher.blinkquestion_set.all()).latest('activate_time')
        #return HttpResponseRedirect(reverse('blink-summary', kwargs={'pk' : latest_round.question.pk}))

        # Else, redirect to waiting room
        return HttpResponseRedirect(reverse('blink-waiting', kwargs={'username' : teacher.user.username }))


def blink_waiting(request,username,assignment=''):

    try:
        teacher = Teacher.objects.get(user__username=username)
    except:
        return HttpResponse('Error')

    return TemplateResponse(
        request,
        'peerinst/blink_waiting.html',
        context=
            {
                'assignment' : assignment,
                'teacher' : teacher,
            },
        )


# AJAX functions
@login_required
def question_search(request):

    if request.method == "GET" and request.user.teacher:
        type = request.GET.get('type',default=None)
        id = request.GET.get('id',default=None)
        search_string = request.GET.get('search_string',default="")
        limit_search = request.GET.get('limit_search',default="false")

        # Exclusions based on type of search
        q_qs = []
        if type == 'blink':
            bq_qs = request.user.teacher.blinkquestion_set.all()
            q_qs = [bq.question.id for bq in bq_qs]
            form_field_name = 'new_blink'

        if type == 'assignment':
            a_qs = Assignment.objects.get(identifier=id).questions.all()
            q_qs = [q.id for q in a_qs]
            form_field_name = 'q'

        # All matching questions
        # TODO: add search on categories
        if limit_search == "true":
            query = Question.objects.filter(Q(text__icontains=search_string) | Q(title__icontains=search_string)).filter(discipline__in=request.user.teacher.disciplines.all()).exclude(id__in=q_qs)
        else:
            query = Question.objects.filter(Q(text__icontains=search_string) | Q(title__icontains=search_string)).exclude(id__in=q_qs)

        if query.count() > 50:
            return TemplateResponse(
                request,
                'peerinst/question_search_error.html',
                context={'count':query.count(),}
                )
        else:
            return TemplateResponse(
                request,
                'peerinst/question_search_results.html',
                context={
                    'search_results':query,
                    'form_field_name':form_field_name,
                    }
                )
    else:
        return HttpResponseRedirect(reverse('access_denied'))


def blink_get_current_url(request,username):
    """View to check current question url for teacher."""

    try:
        # Get teacher
        teacher = Teacher.objects.get(user__username=username)
    except:
        return HttpResponse("Teacher does not exist")

    try:
        # Return url of current active blinkquestion, if any
        blinkquestion = teacher.blinkquestion_set.get(active=True)
        return HttpResponse(reverse('blink-question', kwargs={'pk' : blinkquestion.pk}))
    except:
        try:
            blinkassignment = teacher.blinkassignment_set.get(active=True)
            latest_round = BlinkRound.objects.filter(question__in=teacher.blinkquestion_set.all()).latest('activate_time')
            return HttpResponse(reverse('blink-summary', kwargs={'pk' : latest_round.question.pk}))
        except:
            return HttpResponse("stop")


def blink_count(request,pk):

    blinkquestion = BlinkQuestion.objects.get(pk=pk)
    try:
        blinkround = BlinkRound.objects.get(question=blinkquestion,deactivate_time__isnull=True)
    except:
        try:
            blinkround = BlinkRound.objects.filter(question=blinkquestion).latest('deactivate_time')
        except:
            return JsonResponse()

    context = {}
    context['count'] = BlinkAnswer.objects.filter(voting_round=blinkround).count()

    return JsonResponse(context)


def blink_close(request,pk):

    context = {}

    if request.method=="POST" and request.user.is_authenticated():
        form = forms.BlinkQuestionStateForm(request.POST)
        try:
            blinkquestion = BlinkQuestion.objects.get(pk=pk)
            blinkround = BlinkRound.objects.get(question=blinkquestion,deactivate_time__isnull=True)
            if form.is_valid():
                blinkquestion.active = form.cleaned_data['active']
                blinkquestion.save()
                blinkround.deactivate_time = timezone.now()
                blinkround.save()
                context['state'] = 'success'
            else:
                context['state'] = 'failure'
        except:
            context['state'] = 'failure'

    return JsonResponse(context)


def blink_latest_results(request,pk):

    results = {}

    blinkquestion = BlinkQuestion.objects.get(pk=pk)
    blinkround = BlinkRound.objects.filter(question=blinkquestion).latest('deactivate_time')

    c=1
    for label, text in blinkquestion.question.get_choices():
        results[label] = BlinkAnswer.objects.filter(question=blinkquestion).filter(voting_round=blinkround).filter(answer_choice=c).count()
        c=c+1

    return JsonResponse(results)


def blink_status(request,pk):

    blinkquestion = BlinkQuestion.objects.get(pk=pk)

    response = {}
    response['status'] = blinkquestion.active

    return JsonResponse(response)


# This is a very temporary approach with minimum checking for permissions
@login_required
def blink_reset(request,pk):

    #blinkquestion = BlinkQuestion.objects.get(pk=pk)

    return HttpResponseRedirect(reverse('blink-summary', kwargs={ 'pk' : pk }))


class BlinkAssignmentCreate(LoginRequiredMixin,CreateView):

    model = BlinkAssignment
    fields = ['title']

    def form_valid(self, form):
        key = random.randrange(10000000,99999999)
        while key in BlinkAssignment.objects.all():
            key = random.randrange(10000000,99999999)
        form.instance.key = key
        form.instance.teacher = Teacher.objects.get(user=self.request.user)
        return super(BlinkAssignmentCreate,self).form_valid(form)

    def get_success_url(self):
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            return reverse('blinkAssignment-update', kwargs={'pk': self.object.id})
        except:
            return reverse('welcome')


class BlinkAssignmentUpdate(LoginRequiredMixin,DetailView):

    model = BlinkAssignment

    def get_context_data(self, **kwargs):
        context = super(BlinkAssignmentUpdate, self).get_context_data(**kwargs)
        context['teacher'] = Teacher.objects.get(user=self.request.user)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user.is_authenticated():
            form = forms.RankBlinkForm(request.POST)
            if form.is_valid():

                # Questions can appear in multiple assignments, but only once in each.
                # Get Q for _this_ assignment.
                relationship = form.cleaned_data['q'].get(blinkassignment=self.object)
                operation = form.cleaned_data['rank']
                if operation == "down":
                    relationship.move_down_rank()
                    relationship.save()
                if operation == "up":
                    relationship.move_up_rank()
                    relationship.save()
                if operation == "clear":
                    relationship.delete()
                    relationship.renumber()

                return HttpResponseRedirect(reverse("blinkAssignment-update", kwargs={'pk': self.object.pk}))
            else:
                form = forms.CreateBlinkForm(request.POST)
                if form.is_valid():
                    question = form.cleaned_data['new_blink']
                    key = random.randrange(10000000,99999999)
                    while key in BlinkQuestion.objects.all():
                        key = random.randrange(10000000,99999999)
                    try:
                        blinkquestion = BlinkQuestion(
                            question=question,
                            teacher=Teacher.objects.get(user=self.request.user),
                            time_limit=30,
                            key=key,
                            )
                        blinkquestion.save()

                        if not blinkquestion in self.object.blinkquestions.all():
                            relationship = BlinkAssignmentQuestion(
                                blinkassignment=self.object,
                                blinkquestion=blinkquestion,
                                rank=self.object.blinkquestions.count(),
                            )
                        relationship.save()
                    except:
                        return HttpResponse("error")

                    return HttpResponseRedirect(reverse("blinkAssignment-update", kwargs={'pk': self.object.pk}))
                else:
                    form = forms.AddBlinkForm(request.POST)
                    if form.is_valid():
                        blinkquestion = form.cleaned_data['blink']
                        if not blinkquestion in self.object.blinkquestions.all():
                            relationship = BlinkAssignmentQuestion(
                                blinkassignment=self.object,
                                blinkquestion=blinkquestion,
                                rank=self.object.blinkquestions.count(),
                            )
                            relationship.save()
                        else:
                            return HttpResponse("error")

                        return HttpResponseRedirect(reverse("blinkAssignment-update", kwargs={'pk': self.object.pk}))
                    else:
                        return HttpResponse("error")
        else:
            return HttpResponse("error3")

class DateExtractFunc(Func):
    function = "DATE"

def assignment_timeline_data(request,assignment_id,question_id):
    qs=models.Answer.objects.filter(assignment_id=assignment_id).filter(question_id=question_id)\
    .annotate(date=DateExtractFunc("time"))\
    .values('date')\
    .annotate(N=Count('id'))

    return JsonResponse(list(qs),safe=False)

def network_data(request,assignment_id):
    qs = models.Answer.objects.filter(assignment_id=assignment_id)

    links={}

    for answer in qs:
        if answer.user_token not in links:
            links[answer.user_token]={}
            if answer.chosen_rationale:
                if answer.chosen_rationale.user_token in links[answer.user_token]:
                    links[answer.user_token][answer.chosen_rationale.user_token] += 1
                else:
                    links[answer.user_token][answer.chosen_rationale.user_token] = 1

    # serialize
    links_array = []
    for source,targets in links.items():
        d={}
        for t in targets.keys():
            d['source']=source
            d['target']=t
            d['value']=targets[t]
            links_array.append(d)

    return JsonResponse(links_array,safe=False)
