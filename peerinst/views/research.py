from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Count
from django.forms import (
    ModelForm,
    ModelMultipleChoiceField,
    modelformset_factory,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView

from ..mixins import LoginRequiredMixin, NoStudentsMixin, student_check
from ..models import (
    Answer,
    AnswerAnnotation,
    Assignment,
    Discipline,
    Question,
    QuestionFlag,
    QuestionFlagReason,
    ShownRationale,
)


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def research_index(request):
    template = "peerinst/research/index.html"
    context = {"disciplines": Discipline.objects.all()}
    return render(request, template, context)


def get_question_annotation_counts(discipline_title, annotator, assignment_id):
    """
    Returns:
    ========
    list of dicts, one for each question in discipline, and the counts of
    Answers and AnswerAnnotations for each
    """
    if discipline_title:
        questions_qs = Question.objects.filter(
            discipline__title=discipline_title
        )
    elif assignment_id:
        questions_qs = Assignment.objects.get(
            identifier=assignment_id
        ).questions.order_by("assignmentquestions__rank")

    # FIXME:
    translation_table = str.maketrans("ABCDEFG", "1234567")

    question_annotation_counts = []
    for q in questions_qs:
        d1 = {}
        d1["question"] = q

        d1["question_expert_answers"] = q.answer_set.filter(expert=True)

        # need at least one sample answer that is not marked as expert for each
        # answer choice
        d1["enough_sample_answers"] = 0 not in list(
            q.get_frequency(all_rationales=True)["first_choice"].values()
        )

        d1["total_annotations"] = AnswerAnnotation.objects.filter(
            score__isnull=False, answer__question_id=q.pk
        ).count()
        d1["total_annotations_by_user"] = AnswerAnnotation.objects.filter(
            score__isnull=False, answer__question_id=q.pk, annotator=annotator
        ).count()
        flagged_questions = Question.flagged_objects.all()
        flagged_by_user = QuestionFlag.objects.filter(
            user=annotator
        ).values_list("question", flat=True)
        if q.pk in flagged_by_user:
            d1["flag_color_code"] = "red"
        elif q in flagged_questions:
            d1["flag_color_code"] = "goldenrod"
            d1["flagged_reasons"] = "; ".join(
                [
                    " - ".join(e)
                    for e in QuestionFlag.objects.filter(
                        flag=True, question=q
                    ).values_list("user__username", "flag_reason__title")
                ]
            )
        else:
            d1["flag_color_code"] = None

        answer_frequencies = q.get_frequency_json("first_choice")
        for d2 in answer_frequencies:
            a_choice = str(d2["answer_label"][0]).translate(translation_table)
            d2.update(
                {
                    "annotation_count": AnswerAnnotation.objects.filter(
                        score__isnull=False,
                        answer__question_id=q.pk,
                        answer__first_answer_choice=a_choice,
                    ).count(),
                    "annotation_count_by_user": AnswerAnnotation.objects.filter(  # noqa
                        score__isnull=False,
                        answer__question_id=q.pk,
                        answer__first_answer_choice=a_choice,
                        annotator=annotator,
                    ).count(),
                }
            )
        d1["answerchoices"] = answer_frequencies
        question_annotation_counts.append(d1)

    return question_annotation_counts


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def research_discipline_question_index(
    request, discipline_title=None, assignment_id=None
):
    template = "peerinst/research/question_index.html"

    annotator = get_object_or_404(User, username=request.user)

    question_annotation_counts = get_question_annotation_counts(
        discipline_title=discipline_title,
        annotator=annotator,
        assignment_id=assignment_id,
    )
    request.session["assignment_id"] = assignment_id

    context = {
        "questions": question_annotation_counts,
        "discipline_title": discipline_title,
        "assignment_id": assignment_id,
        "annotations_count": AnswerAnnotation.objects.filter(
            annotator=annotator, score__isnull=False
        ).count(),
        "annotator": annotator,
    }
    return render(request, template, context)


@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def research_question_answer_list(
    request,
    question_pk,
    answerchoice_value,
    discipline_title=None,
    assignment_id=None,
):
    template = "peerinst/research/answer_list.html"
    if discipline_title:
        reverse_url_name = "research-question-answer-list-by-discipline"
    elif assignment_id:
        reverse_url_name = "research-question-answer-list-by-assignment"

    annotator = get_object_or_404(User, username=request.user)
    if not annotator:
        logout(request)
        raise PermissionDenied

    # FIXME
    if answerchoice_value.isdigit():
        answerchoice_id = answerchoice_value
    else:
        answerchoice_id = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}[
            answerchoice_value
        ]

    answer_qs = Question.objects.get(pk=question_pk).answer_set.filter(
        question_id=question_pk, first_answer_choice=answerchoice_id
    )
    for a in answer_qs:
        annotation, created = AnswerAnnotation.objects.get_or_create(
            answer=a,
            annotator=annotator,
        )

    # only need two expert scores per rationale,
    # and those marked never show even by one person can be excluded
    already_scored = (
        AnswerAnnotation.objects.filter(
            answer__question_id=question_pk,
            score__isnull=False,
            answer__first_answer_choice=answerchoice_id,
        )
        .values("answer")
        .order_by("answer")
        .annotate(times_scored=Count("answer"))
        .filter(times_scored__gte=3)
        .values_list("answer__id", flat=True)
    )

    queryset = (
        AnswerAnnotation.objects.filter(
            answer__question_id=question_pk,
            annotator=annotator,
            answer__first_answer_choice=answerchoice_id,
        )
        .exclude(answer__id__in=already_scored)
        .annotate(times_shown=Count("answer__shown_answer"))
        .order_by("-times_shown")
    )

    AnswerAnnotationFormset = modelformset_factory(
        AnswerAnnotation, fields=("score",), extra=0
    )

    formset = AnswerAnnotationFormset(queryset=queryset)

    context = {
        "formset": formset,
        "question": Question.objects.get(id=question_pk),
        "discipline_title": discipline_title,
        "question_pk": question_pk,
        "assignment_id": assignment_id,
        "annotations_count": AnswerAnnotation.objects.filter(
            annotator=annotator,
            score__isnull=False,
            answer__question_id=question_pk,
            answer__first_answer_choice=answerchoice_id,
        ).count(),
        "annotator": annotator,
    }

    if request.method == "POST":
        formset = AnswerAnnotationFormset(request.POST)
        if formset.is_valid():
            instances = formset.save()
            context.update(message=_("Scores updated"))

    return render(request, template, context)


def research_all_annotations_for_question(
    request, question_pk, discipline_title=None, assignment_id=None
):
    """
    Returns:
    ====================
    All answer annotations for a question, ordered for
    comparison by researchers
    """
    template = "peerinst/research/all_annotations.html"
    question = Question.objects.get(id=question_pk)
    context = {
        "question": question,
        "question_pk": question_pk,
        "discipline_title": discipline_title,
        "assignment_id": assignment_id,
    }

    all_annotations = []
    for label, answerchoice_text in question.get_choices():
        d1 = {}
        d1["answerchoice"] = label
        d1["annotations"] = []

        # FIXME
        if label.isdigit():
            answerchoice_id = label
        else:
            answerchoice_id = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}[
                label
            ]

        a_list = list(
            set(
                AnswerAnnotation.objects.filter(
                    score__isnull=False,
                    answer__question_id=question_pk,
                    answer__first_answer_choice=answerchoice_id,
                ).values_list("answer", flat=True)
            )
        )

        a_list.sort()

        for a in a_list:
            d2 = {}
            d2["answer"] = Answer.objects.get(pk=a)
            d2["scores"] = AnswerAnnotation.objects.filter(
                answer=a, score__isnull=False
            ).values("score", "annotator__username")
            d2["times_shown"] = ShownRationale.objects.filter(
                shown_answer=a
            ).count()
            d2["times_chosen"] = Answer.objects.filter(
                chosen_rationale_id=a
            ).count()
            d1["annotations"].append(d2)

        all_annotations.append(d1)

    context["all_annotations"] = all_annotations

    return render(request, template, context)


class QuestionFlagForm(ModelForm):
    flag_reason = ModelMultipleChoiceField(
        queryset=QuestionFlagReason.objects.all()
    )

    class Meta:
        model = QuestionFlag
        fields = ["flag", "flag_reason", "comment"]


@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def flag_question_form(
    request, question_pk, discipline_title=None, assignment_id=None
):
    """
    Get or Create QuestionFlag object for user, and allow edit
    """
    template = "peerinst/research/flag_question.html"
    question = get_object_or_404(Question, pk=question_pk)
    message = None

    try:
        question_flag = QuestionFlag.objects.get(
            user=request.user, question=question
        )
    except ObjectDoesNotExist:
        question_flag = None

    if request.method == "GET":
        form = QuestionFlagForm(instance=question_flag)

    if request.method == "POST":
        form = QuestionFlagForm(request.POST, instance=question_flag)

        if form.is_valid():
            form.instance.user = request.user
            form.instance.question = question
            instance = form.save()
            if instance.flag:
                message = _(
                    """
                    You have flagged this question, and your input
                    has been forwarded to a myDALITE content moderator.
                    """
                )
            else:
                message = _(
                    """
                    You have un-flagged this question, and thus it will be
                    taken off the list of potentially problematic questions.
                    """
                )

    context = {
        "form": form,
        "question": question,
        "message": message,
        "discipline_title": discipline_title,
        "assignment_id": assignment_id,
        "expert_answers": question.answer_set.filter(expert=True),
    }

    return render(request, template, context)


class AnswerExpertUpdateView(LoginRequiredMixin, NoStudentsMixin, UpdateView):
    model = Answer
    fields = ["expert"]
    template_name = "peerinst/research/answer-expert-update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teacher"] = self.request.user.teacher
        context["question"] = Question.objects.get(pk=self.object.question_id)
        return context

    def get_success_url(self):
        return reverse(
            "research-fix-expert-rationale",
            kwargs={"question_id": self.object.question_id},
        )
