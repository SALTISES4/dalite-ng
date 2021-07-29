import collections
import itertools
import re
import urllib.error
import urllib.parse
import urllib.request

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from . import models
from .admin import AnswerAdmin
from .forms import (
    AssignmentMultiselectForm,
    FirstAnswerForm,
    StudentGroupAssignmentManagementForm,
)
from .mixins import (
    LoginRequiredMixin,
    NoStudentsMixin,
    TOSAcceptanceRequiredMixin,
)
from .util import make_percent_function, student_list_from_student_groups


class StaffMemberRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(StaffMemberRequiredMixin, cls).as_view(**initkwargs)
        return staff_member_required(view)


class AdminIndexView(StaffMemberRequiredMixin, TemplateView):
    template_name = "admin/peerinst/index.html"

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context.update(assignments=models.Assignment.objects.all())
        return context


def get_question_aggregates(assignment, question, student_groups=None):
    """
    Get aggregate statistics for the given assignment and question.  This
    function returns a pair (sums, students), where 'sums' is a
    collections.Counter object mapping labels to integers, and 'students' is
    the set of all user tokens of the submitted answers.
    """
    # Get indices of the correct answer choices (usually only one)
    answerchoice_correct = question.answerchoice_set.values_list(
        "correct", flat=True
    )
    correct_choices = list(
        itertools.compress(itertools.count(1), answerchoice_correct)
    )
    if not student_groups:
        # Select answers entered by students, not example answers
        answers = question.answer_set.filter(assignment=assignment).exclude(
            user_token=""
        )
    else:
        student_ids = student_list_from_student_groups(student_groups)
        answers = (
            question.answer_set.filter(assignment=assignment)
            .exclude(user_token="")
            .filter(user_token__in=student_ids)
        )

    switched_answers = answers.exclude(
        second_answer_choice=F("first_answer_choice")
    )
    sums = collections.Counter(
        total_answers=answers.count(),
        correct_first_answers=answers.filter(
            first_answer_choice__in=correct_choices
        ).count(),
        correct_second_answers=answers.filter(
            second_answer_choice__in=correct_choices
        ).count(),
        switches=switched_answers.count(),
    )
    for choice_index in range(1, question.answerchoice_set.count() + 1):
        key = ("switches", choice_index)
        count = switched_answers.filter(
            second_answer_choice=choice_index
        ).count()
        if count:
            sums[key] = count
    # Get a set of all user tokens.  DISTINCT queries are not implemented for
    # MySQL, so this is the only way I can think of to determine the number of
    # students who answered at least one question in an assignment.
    students = set(answers.values_list("user_token", flat=True))
    return sums, students


def get_assignment_aggregates(assignment, student_groups=None):
    """
    Get aggregate statistics for the given assignment.  This function returns a
    pair (sums, question_data), where sums is a collections.Counter object
    mapping labels to integers, and question_data is a list of pairs (question,
    sums) with the sums for the respective question.
    """
    sums = collections.Counter()
    students = set()
    question_data = []
    for question in assignment.questions.order_by("assignmentquestions__rank"):
        q_sums, q_students = get_question_aggregates(
            assignment, question, student_groups
        )
        sums += q_sums
        students |= q_students
        q_sums.update(total_students=len(q_students))
        question_data.append((question, q_sums))
    sums.update(total_students=len(students))
    return sums, question_data


def get_question_rationale_aggregates(
    assignment,
    question,
    perpage,
    choice_id=None,
    include_own_rationales=False,
    student_groups=None,
):
    """
    Get the top `perpage` rationales for answers to the given assignment and
    question.

    This function returns a pair (sums, rationales), with entries for these
    groups of rationales:
    * 'upvoted': upvoted rationales
    * 'chosen': chosen rationales for all answers to the given question
    * 'right_to_wrong': chosen rationales for answers that switched from right
                        to wrong
    * 'wrong_to_right': chosen rationales for answers that switched from wrong
                        to right

    `perpage` limits the number of rationales returned, but does not affect the
    counts in the returned `sums`.

    'sums' is a collection.Counter object mapping the above rationale group
    labels to total rationale counts.

    'rationales' is a dict keyed by the above rational group labels.  The
    values are sorted lists of dicts:

        {
        'upvoted': [
            {
                'rationale': <obj>, # instance of model.Answer
                'count': <int>,     # number of times 'rationale' was upvoted
            },
            ...
        ],
        'chosen': [
            {
                'rationale': <obj>, # instance of model.Answer or None
                'count': <int>,     # number of times 'rationale' was chosen
            },
            ...
        ],
        ...
        }

    """
    if not student_groups:
        # Select answers entered by students, not example answers
        answers = question.answer_set.filter(assignment=assignment).exclude(
            user_token=""
        )
    else:
        student_ids = student_list_from_student_groups(student_groups)
        answers = (
            question.answer_set.filter(assignment=assignment)
            .exclude(user_token="")
            .filter(user_token__in=student_ids)
        )

    if choice_id is not None:
        # Filter the answers we look at to just those who eventually chose
        # the option we're interested in - we want to know which rationales
        # were convincing for this answer.
        answers = answers.filter(second_answer_choice=choice_id)

    # Get indices of the correct answer choice(s)
    answerchoice_correct = question.answerchoice_set.values_list(
        "correct", flat=True
    )
    correct_choices = list(
        itertools.compress(itertools.count(1), answerchoice_correct)
    )

    # Helper function collects chosen rationales and the number of times used
    # from a list of answers
    def _top_rationales(answer_list):
        # Count the chosen rationales for the given answer list, counting the
        # answer's original rationale if there's no related chosen rationale
        # (the student stuck with their original rationale) and the function
        # was called with include_own_rationales=True
        counts = collections.Counter(
            a.chosen_rationale
            or (
                # If a.chosen_rationale isn't truthy (in other words, if it is
                # None), count a itself if include_own_rationales is True;
                # otherwise, count None
                a
                if include_own_rationales
                else None
            )
            for a in answer_list.select_related("chosen_rationale")
        )

        # Return a list of dicts, sorted by descending count
        sorted_list = [
            dict(rationale=rationale, count=counts[rationale])
            for rationale in sorted(counts, key=counts.get, reverse=True)
        ]
        return sorted_list[:perpage], len(sorted_list)

    # Collect the upvoted rationales, sorted by descending upvotes
    output = {"upvoted": []}
    upvoted = answers.exclude(upvotes=0).order_by("-upvotes")
    for rationale in upvoted.all()[:perpage]:
        output["upvoted"].append(
            {"rationale": rationale, "count": rationale.upvotes}
        )

    # Show totals in the sums counter
    sums = collections.Counter()
    sums["upvoted"] = upvoted.count()

    # Collect top rationales chosen for all answers
    output["chosen"], sums["chosen"] = _top_rationales(answers)

    # Collect top rationales chosen for answers switched from wrong to right
    wrong_to_right = answers.exclude(
        first_answer_choice__in=correct_choices
    ).filter(second_answer_choice__in=correct_choices)
    output["wrong_to_right"], sums["wrong_to_right"] = _top_rationales(
        wrong_to_right
    )

    # Collect top rationales chosen for answers switched from right to wrong
    right_to_wrong = answers.exclude(
        second_answer_choice__in=correct_choices
    ).filter(first_answer_choice__in=correct_choices)
    output["right_to_wrong"], sums["right_to_wrong"] = _top_rationales(
        right_to_wrong
    )

    # Return the sums and final sorted lists of rationales
    return sums, output


class QuestionRationaleView(StaffMemberRequiredMixin, TemplateView):
    template_name = "admin/peerinst/question/rationales.html"

    @staticmethod
    def prepare_summary_data(sums):
        return [
            (_("Total rationales upvoted"), sums["upvoted"]),
            (_("Total rationales chosen"), sums["chosen"]),
            (
                _(
                    "Total rationales chosen for right to wrong answer "
                    "switches"
                ),
                sums["right_to_wrong"],
            ),
            (
                _(
                    "Total rationales chosen for wrong to right answer "
                    "switches"
                ),
                sums["wrong_to_right"],
            ),
        ]

    @staticmethod
    def prepare_rationale_labels():
        return [
            _("Count"),
            _("Rationale"),
            _("Upvotes"),
            _("Downvotes"),
            _("Answers with this chosen rationale"),
        ]

    @staticmethod
    def prepare_rationale_rows(rationale_data=None):
        rows = []
        for item in rationale_data:
            count = item.get("count", 0)
            rationale = item.get("rationale", None)
            if rationale:
                row = dict(
                    data=[
                        count,
                        rationale.rationale,
                        rationale.upvotes,
                        rationale.downvotes,
                    ],
                    link_answers="?".join(
                        [
                            reverse("admin:peerinst_answer_changelist"),
                            urllib.parse.urlencode(
                                dict(chosen_rationale__id__exact=rationale.id)
                            ),
                        ]
                    ),
                )
            else:
                row = dict(
                    data=[
                        count,
                        _("(Student stuck to own rationale)"),
                        "",
                        "",
                    ],
                    link_answers="?".join(
                        [
                            reverse("admin:peerinst_answer_changelist"),
                            urllib.parse.urlencode(
                                dict(chosen_rationale__isnull=True)
                            ),
                        ]
                    ),
                )
            rows.append(row)

        return rows

    def prepare_rationale_data(self, rationale_data):
        return [
            {
                "heading": _("Upvoted rationales"),
                "labels": self.prepare_rationale_labels(),
                "rows": self.prepare_rationale_rows(rationale_data["upvoted"]),
            },
            {
                "heading": _("Top rationales chosen"),
                "labels": self.prepare_rationale_labels(),
                "rows": self.prepare_rationale_rows(rationale_data["chosen"]),
            },
            {
                "heading": _(
                    "Top rationales chosen for right to wrong answer switches"
                ),
                "labels": self.prepare_rationale_labels(),
                "rows": self.prepare_rationale_rows(
                    rationale_data["right_to_wrong"]
                ),
            },
            {
                "heading": _(
                    "Top rationales chosen for wrong to right answer switches"
                ),
                "labels": self.prepare_rationale_labels(),
                "rows": self.prepare_rationale_rows(
                    rationale_data["wrong_to_right"]
                ),
            },
        ]

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        assignment_id = self.kwargs["assignment_id"]
        assignment = get_object_or_404(
            models.Assignment, identifier=assignment_id
        )
        question_id = self.kwargs["question_id"]
        question = get_object_or_404(models.Question, id=question_id)

        # Limit number of rationales shown to a number between [0,
        # AnswerAdmin.list_per_page]
        perpage = self.request.GET.get("perpage")
        try:
            perpage = int(perpage)
        except (TypeError, ValueError):
            perpage = None
        if (
            (perpage is None)
            or (perpage <= 0)
            or (perpage > AnswerAdmin.list_per_page)
        ):
            perpage = AnswerAdmin.list_per_page

        sums, rationale_data = get_question_rationale_aggregates(
            assignment, question, perpage
        )
        context.update(
            assignment=assignment,
            question=question,
            summary_data=self.prepare_summary_data(sums),
            rationale_data=self.prepare_rationale_data(rationale_data),
            perpage=perpage,
        )
        return context


class AssignmentResultsViewBase(TemplateView):
    def prepare_stats(self, sums, switch_columns):
        total_answers = sums["total_answers"]
        percent = make_percent_function(total_answers)
        results = [
            total_answers,
            sums["total_students"],
            sums["correct_first_answers"],
            percent(sums["correct_first_answers"]),
            sums["correct_second_answers"],
            percent(sums["correct_second_answers"]),
            sums["switches"],
            percent(sums["switches"]),
        ]
        for choice_index in switch_columns:
            results.append(sums.get(("switches", choice_index), ""))
        return results

    def prepare_assignment_data(self, sums, switch_columns):
        labels = [
            _("Total number of answers recorded:"),
            _("Total number of participating students:"),
            _("Correct answer choices – first attempt:"),
            _("↳ Percentage of total answers:"),
            _("Correct answer choices – second attempt:"),
            _("↳ Percentage of total answers:"),
            _("Number of answer choice switches:"),
            _("↳ Percentage of total answers:"),
        ]
        for choice_index in switch_columns:
            labels.append(
                _("Switches to answer {index}:").format(index=choice_index)
            )
        return list(zip(labels, self.prepare_stats(sums, switch_columns)))

    def prepare_question_data(self, question_data, switch_columns):
        rows = []
        for i, (question, sums) in enumerate(question_data, 1):
            get_params_this = urllib.parse.urlencode(
                dict(assignment=self.assignment_id, question=question.id)
            )
            get_params_all = urllib.parse.urlencode(dict(question=question.id))
            rows.append(
                dict(
                    data=[i, question.title]
                    + self.prepare_stats(sums, switch_columns),
                    link_this="?".join(
                        [
                            reverse("admin:peerinst_answer_changelist"),
                            get_params_this,
                        ]
                    ),
                    link_all="?".join(
                        [
                            reverse("admin:peerinst_answer_changelist"),
                            get_params_all,
                        ]
                    ),
                    link_rationales=reverse(
                        "question-rationales",
                        kwargs={
                            "assignment_id": self.assignment_id,
                            "question_id": question.id,
                        },
                    ),
                )
            )
        labels = [
            _("No."),
            _("Question ID"),
            _("Total answers"),
            _("Total students"),
            _("First correct"),
            _("Percent"),
            _("Second correct"),
            _("Percent"),
            _("Switches"),
            _("Percent"),
        ]
        for choice_index in switch_columns:
            labels.append(_("To {index}").format(index=choice_index))
        labels.append(_("Show answers"))
        return dict(labels=labels, rows=rows)

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        self.assignment_id = self.kwargs["assignment_id"]
        assignment = get_object_or_404(
            models.Assignment, identifier=self.assignment_id
        )
        sums, question_data = get_assignment_aggregates(assignment)
        switch_columns = sorted(
            k[1] for k in sums if isinstance(k, tuple) and k[0] == "switches"
        )
        context.update(
            assignment=assignment,
            assignment_data=self.prepare_assignment_data(sums, switch_columns),
            question_data=self.prepare_question_data(
                question_data, switch_columns
            ),
        )
        return context


class AssignmentResultsView(
    StaffMemberRequiredMixin, AssignmentResultsViewBase
):
    template_name = "admin/peerinst/assignment_results.html"


class QuestionPreviewForm(FirstAnswerForm):

    expert = forms.BooleanField(
        label=_("Expert answer"), initial=True, required=False
    )


class ExpertRationaleForm(QuestionPreviewForm):
    """
    Special form for entering Expert Rationales for correct answers only
    Requires a diffent __init__ as the form depends on the question for
    determining the correct answer_choices
    """

    def __init__(self, answer_choices, question, *args, **kwargs):
        choice_texts = [
            mark_safe(
                ". ".join(
                    (
                        pair[0],
                        ("<br>" + "&nbsp" * 5).join(
                            re.split(r"<br(?: /)?>", pair[1])
                        ),
                    )
                )
            )
            for pair in answer_choices
        ]
        #  choice_texts = [mark_safe(". ".join(pair)) for pair in
        #  answer_choices]
        all_choices = enumerate(choice_texts, 1)
        correct_choices = list(
            itertools.compress(
                all_choices,
                question.answerchoice_set.all().values_list(
                    "correct", flat=True
                ),
            )
        )
        self.base_fields["first_answer_choice"].choices = correct_choices
        forms.Form.__init__(self, *args, **kwargs)


class QuestionPreviewViewBase(
    LoginRequiredMixin, NoStudentsMixin, TOSAcceptanceRequiredMixin, FormView
):
    """Non-admin base view for question preview and sample answer form."""

    template_name = "peerinst/question/preview.html"
    form_class = QuestionPreviewForm

    def get_form_kwargs(self):
        self.question = get_object_or_404(
            models.Question, pk=self.kwargs["question_id"]
        )
        self.answer_choices = self.question.get_choices()
        kwargs = super(QuestionPreviewViewBase, self).get_form_kwargs()
        kwargs.update(answer_choices=self.answer_choices)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionPreviewViewBase, self).get_context_data(
            **kwargs
        )
        if self.question.get_frequency(all_rationales=True)["first_choice"]:
            save_allowed = 0 not in list(
                self.question.get_frequency(all_rationales=True)[
                    "first_choice"
                ].values()
            )
        else:
            save_allowed = False

        assignment_form = AssignmentMultiselectForm(
            self.request.user, self.question
        )
        context.update(
            question=self.question,
            answer_choices=self.answer_choices,
            assignment_form=assignment_form,
            assignment_count=assignment_form.queryset.count(),
            save_allowed=save_allowed,
        )
        # reset session variable that may have been set in Quality Control /
        # research_discipline_question_index view
        self.request.session["assignment_id"] = None

        return context

    def form_valid(self, form):
        """
        These rationales are NOT saved as expert, as that is reserved for a
        seperate form
        """
        answer = models.Answer(
            question=self.question,
            first_answer_choice=int(form.cleaned_data["first_answer_choice"]),
            rationale=form.cleaned_data["rationale"],
            show_to_others=True,
            expert=False,
        )
        answer.save()
        messages.add_message(
            self.request, messages.INFO, _("Sample answer saved.")
        )
        return super(QuestionPreviewViewBase, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            "sample-answer-form", kwargs=dict(question_id=self.question.pk)
        )


class QuestionPreviewView(StaffMemberRequiredMixin, QuestionPreviewViewBase):
    template_name = "admin/peerinst/question/preview.html"

    def get_success_url(self):
        return reverse(
            "question-preview", kwargs=dict(question_id=self.question.pk)
        )


class QuestionExpertRationaleView(QuestionPreviewViewBase):
    """
    Special view for entering Expert Rationales for correct answers only
    Requires that question is added to form kwargs, and template variables to
    block completion buttons unless enough expert rationales are entered
    """

    template_name = "peerinst/question/fix_expert_rationales.html"
    form_class = ExpertRationaleForm

    def get_form_kwargs(self):
        """
        add question to form kwargs
        """
        kwargs = super(QuestionExpertRationaleView, self).get_form_kwargs()
        kwargs.update(question=self.question)
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Show currently saved expert rationales, and define context variable
        that does not render completion button until an expert rationale exists
        for each correct answerchoice.
        """

        context = super(QuestionExpertRationaleView, self).get_context_data(
            **kwargs
        )
        answerchoice_correct = self.question.answerchoice_set.values_list(
            "correct", flat=True
        )
        correct_answer_choices = list(
            itertools.compress(itertools.count(1), answerchoice_correct)
        )
        expert_rationales = self.question.answer_set.filter(expert=True)

        save_allowed = all(
            [
                cac
                in expert_rationales.values_list(
                    "first_answer_choice", flat=True
                )
                for cac in correct_answer_choices
            ]
        )
        assignment_id = self.request.session.get("assignment_id")
        question_id = self.request.session.get("question_id")
        context.update(
            expert_rationales=expert_rationales,
            save_allowed=save_allowed,
            assignment_id=assignment_id,
            question_id=question_id,
        )
        return context

    def form_valid(self, form):
        """
        save answer as expert = True
        """
        answer = models.Answer(
            question=self.question,
            first_answer_choice=int(form.cleaned_data["first_answer_choice"]),
            rationale=form.cleaned_data["rationale"],
            show_to_others=True,
            expert=True,
        )
        answer.save()
        messages.add_message(
            self.request, messages.INFO, _("Expert rationale saved.")
        )
        return super(QuestionPreviewViewBase, self).form_valid(form)

    def get_success_url(self):
        if self.kwargs.get("assignment_id"):
            return reverse(
                "research-fix-expert-rationale",
                kwargs=dict(
                    question_id=self.question.pk,
                    assignment_id=self.kwargs.get("assignment_id"),
                ),
            )
        else:
            return reverse(
                "research-fix-expert-rationale",
                kwargs=dict(question_id=self.question.pk),
            )


class StringListForm(forms.Form):
    """Simple form to allow entering a list of strings in a textarea widget."""

    strings = forms.CharField(widget=forms.Textarea)

    def __init__(self, initial, *args, **kwargs):
        if "strings" in initial:
            initial["strings"] = "\n".join(initial["strings"])
        forms.Form.__init__(self, initial=initial, *args, **kwargs)

    def clean(self):
        cleaned_data = super(StringListForm, self).clean()
        strings = []
        for s in cleaned_data["strings"].splitlines():
            s = s.strip()
            if s:
                strings.append(s)
        cleaned_data["strings"] = strings
        return cleaned_data


class StringListView(StaffMemberRequiredMixin, FormView):
    template_name = "admin/peerinst/string_list.html"
    form_class = StringListForm
    model_class = None  # to be set on subclasses

    def get_initial(self):
        self.initial_strings = self.model_class.objects.values_list(
            "name", flat=True
        )
        return {"strings": self.initial_strings}

    def get_context_data(self, **kwargs):
        context = super(StringListView, self).get_context_data(**kwargs)
        context.update(
            model_name_plural=self.model_class._meta.verbose_name_plural
        )
        return context

    def form_valid(self, form):
        new_strings = form.cleaned_data["strings"]
        already_added = set(self.initial_strings)
        self.model_class.objects.filter(
            name__in=already_added - set(new_strings)
        ).delete()
        for new in new_strings:
            if new in already_added:
                continue
            self.model_class(name=new).save()
            already_added.add(new)
        messages.add_message(
            self.request,
            messages.INFO,
            _("List of {model_name} saved.").format(
                model_name=self.model_class._meta.verbose_name_plural
            ),
        )
        return super(StringListView, self).form_valid(form)

    def get_success_url(self):
        return reverse("admin-index")


class FakeUsernames(StringListView):
    model_class = models.FakeUsername


class FakeCountries(StringListView):
    model_class = models.FakeCountry


def aggregate_fake_attribution_data(votes_qs):
    def update_aggregates(data, key, vote_type):
        aggregates = data.get(key)
        if aggregates is None:
            aggregates = data[key] = {
                "total": 0,
                models.AnswerVote.UPVOTE: 0,
                models.AnswerVote.DOWNVOTE: 0,
                models.AnswerVote.FINAL_CHOICE: 0,
            }
        aggregates["total"] += 1
        aggregates[vote_type] += 1

    # We are using plain dictionaries instead of collections.defaultdict for
    # perfromance reasons.
    username_data = {}
    country_data = {}
    for answer_vote in votes_qs.iterator():
        vote_type = answer_vote.vote_type
        update_aggregates(username_data, answer_vote.fake_username, vote_type)
        update_aggregates(country_data, answer_vote.fake_country, vote_type)
    return username_data, country_data


class AttributionAnalysisFilterForm(forms.Form):
    assignment = forms.ModelChoiceField(
        models.Assignment.objects.all(),
        empty_label=_("---all---"),
        required=False,
    )
    question = forms.ModelChoiceField(
        models.Question.objects.all(),
        empty_label=_("---all---"),
        required=False,
    )


class AttributionAnalysis(TemplateView):
    template_name = "admin/peerinst/attribution_analysis.html"

    def get_aggregates(self, form_data):
        def extract_columns(name, stats):
            percent = make_percent_function(stats["total"])
            return (
                name,
                stats["total"],
                stats[models.AnswerVote.UPVOTE],
                percent(stats[models.AnswerVote.UPVOTE]),
                stats[models.AnswerVote.DOWNVOTE],
                percent(stats[models.AnswerVote.DOWNVOTE]),
                stats[models.AnswerVote.FINAL_CHOICE],
                percent(stats[models.AnswerVote.FINAL_CHOICE]),
            )

        assignment = form_data["assignment"]
        question = form_data["question"]
        filters = {}
        if assignment is not None:
            filters["assignment"] = assignment
        if question is not None:
            filters["answer__question"] = question
        votes_qs = models.AnswerVote.objects.filter(**filters)
        username_data, country_data = aggregate_fake_attribution_data(votes_qs)
        username_data_table = list(
            itertools.starmap(extract_columns, sorted(username_data.items()))
        )
        country_data_table = list(
            itertools.starmap(extract_columns, sorted(country_data.items()))
        )
        return username_data_table, country_data_table

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        form = AttributionAnalysisFilterForm(data=self.request.GET)
        if form.is_valid() and self.request.GET:
            (
                context["username_data"],
                context["country_data"],
            ) = self.get_aggregates(form.cleaned_data.copy())
        context.update(form=form)
        return context


class StudentGroupAssignmentManagement(StaffMemberRequiredMixin, TemplateView):
    template_name = "admin/peerinst/group_assignment_management.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = StudentGroupAssignmentManagementForm(self.request.POST)
        if form.is_valid():
            group_assignment = form.cleaned_data["group_assignment"]
            group = group_assignment.group
            student_list = models.Student.objects.filter(groups=group)

            count_assignments_created = 0
            count_emails_sent = 0
            for student in student_list:
                # Create missing instances
                if not models.StudentAssignment.objects.filter(
                    student=student, group_assignment=group_assignment
                ).exists():
                    assignment_ = models.StudentAssignment.objects.create(
                        student=student, group_assignment=group_assignment
                    )
                    count_assignments_created += 1
                    # Send email
                    if (
                        not student.student.email.endswith("localhost")
                        and not group_assignment.expired
                    ):
                        assignment_.send_email("new_assignment")
                        count_emails_sent += 1

            student_assignment_list = models.StudentAssignment.objects.filter(
                student__in=student_list, group_assignment=group_assignment
            )
            context.update(assignments_created=count_assignments_created)
            context.update(emails_sent=count_emails_sent)
            context.update(group=group)
            context.update(group_assignment=group_assignment)
            context.update(student_list=student_list)
            context.update(student_assignment_list=student_assignment_list)

        context.update(form=form)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)

        form = StudentGroupAssignmentManagementForm()
        group = None
        group_assignment = None
        student_list = None
        student_assignment_list = None

        if self.request.GET:
            form = StudentGroupAssignmentManagementForm(data=self.request.GET)
            if form.is_valid():
                group_assignment = form.cleaned_data["group_assignment"]
                group = group_assignment.group
                student_list = models.Student.objects.filter(groups=group)
                student_assignment_list = (
                    models.StudentAssignment.objects.filter(  # noqa
                        student__in=student_list,
                        group_assignment=group_assignment,
                    )
                )

        context.update(form=form)
        context.update(group=group)
        context.update(group_assignment=group_assignment)
        context.update(student_list=student_list)
        context.update(student_assignment_list=student_assignment_list)

        return context
