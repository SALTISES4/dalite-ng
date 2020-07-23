import re
from datetime import datetime, date

import pytz
from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import (
    Assignment,
    BlinkAssignmentQuestion,
    BlinkQuestion,
    Category,
    Discipline,
    Question,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)


class NonStudentPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        active_users = User.objects.filter(email__iexact=email, is_active=True)

        return (
            u
            for u in active_users
            if u.has_usable_password() and not hasattr(u, "student")
        )


class FirstAnswerForm(forms.Form):
    """Form to select one of the answer choices and enter a rationale."""

    error_css_class = "validation-error"

    first_answer_choice = forms.ChoiceField(
        label=_("Choose one of these answers:"),
        widget=forms.RadioSelect,
        error_messages={
            "required": _("Please make sure to select an answer choice.")
        },
    )
    rationale = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 100, "rows": 7})
    )

    def __init__(self, answer_choices, *args, **kwargs):
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
        self.base_fields["first_answer_choice"].choices = enumerate(
            choice_texts, 1
        )
        forms.Form.__init__(self, *args, **kwargs)


class RationaleOnlyForm(forms.Form):
    rationale = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 100, "rows": 7})
    )
    datetime_start = forms.CharField(
        widget=forms.HiddenInput(), initial=datetime.now(pytz.utc)
    )

    def __init__(self, answer_choices, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)


class ReviewAnswerForm(forms.Form):
    """Form on the answer review page."""

    error_css_class = "validation-error"

    second_answer_choice = forms.ChoiceField(
        label="", widget=forms.RadioSelect
    )

    shown_rationales = []

    RATIONALE_CHOICE = "rationale_choice"

    def __init__(self, rationale_choices, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        answer_choices = []
        rationale_choice_fields = []
        show_more_counters = []
        show_more_labels = []
        rationale_id_list = []
        for i, (choice, label, rationales) in enumerate(rationale_choices):
            rationales = [
                (id_ if id_ is not None else "None", rationale)
                for id_, rationale in rationales
            ]
            rationale_ids = [
                (id_ if id_ is not None else "None")
                for id_, rationale in rationales
            ]

            field_name = "{}_{}".format(self.RATIONALE_CHOICE, i)
            self.fields[field_name] = forms.ChoiceField(
                label="",
                required=False,
                widget=forms.RadioSelect,
                choices=rationales,
            )
            show_more_field_name = "show-more-counter-" + str(i + 1)
            self.fields[show_more_field_name] = forms.IntegerField(
                required=False, initial=2
            )
            show_more_counters.append(self[show_more_field_name])
            show_more_labels.append(show_more_field_name)
            answer_choices.append((choice, label))
            rationale_choice_fields.append(self[field_name])
            rationale_id_list.append(rationale_ids)
        self.fields["second_answer_choice"].choices = answer_choices
        self.rationale_groups = list(
            zip(
                self["second_answer_choice"],
                rationale_choice_fields,
                show_more_counters,
                show_more_labels,
                rationale_id_list,
            )
        )

    def clean(self):
        cleaned_data = forms.Form.clean(self)
        shown_rationales = []
        if cleaned_data is not None:
            for (
                answer_choice,
                rationale_choice_field,
                show_more_counter,
                label,
                rationale_ids,
            ) in self.rationale_groups:
                for i in (
                    range(cleaned_data[label])
                    if cleaned_data[label]
                    else range(min(2, len(rationale_ids)))
                ):
                    if (
                        rationale_ids[i] is not None
                        and rationale_ids[i] != "None"
                    ):
                        shown_rationales.append(rationale_ids[i])
        self.shown_rationales = shown_rationales if shown_rationales else None
        rationale_choices = [
            value
            for key, value in cleaned_data.items()
            if key.startswith(self.RATIONALE_CHOICE)
        ]
        if sum(map(bool, rationale_choices)) != 1:
            # This should be prevented by the UI on the client side, so this
            # check is mostly to
            # protect against bugs and people transferring made-up data.
            raise forms.ValidationError(
                _("Please select exactly one rationale.")
            )
        chosen_rationale_id = next(
            value for value in rationale_choices if value
        )
        cleaned_data.update(chosen_rationale_id=chosen_rationale_id)
        return cleaned_data


class SequentialReviewForm(forms.Form):
    """Form to vote on a single rationale."""

    def clean(self):
        cleaned_data = forms.Form.clean(self)
        if "upvote" in self.data:
            cleaned_data["vote"] = "up"
        elif "downvote" in self.data:
            cleaned_data["vote"] = "down"
        else:
            raise forms.ValidationError(_("Please vote up or down."))
        return cleaned_data


class AssignmentCreateForm(forms.ModelForm):
    """Simple form to create a new Assignment"""

    class Meta:
        model = Assignment
        fields = ["identifier", "title"]


class AssignmentMultiselectForm(forms.Form):
    def __init__(self, user=None, question=None, *args, **kwargs):
        super(AssignmentMultiselectForm, self).__init__(*args, **kwargs)
        if user:
            # Remove assignments with question and assignments with student
            # answers
            queryset = user.assignment_set.all()
        else:
            queryset = Assignment.objects.all()

        num_student_rationales = Count(
            "answer", filter=~Q(answer__user_token="")
        )

        if question:
            queryset = (
                queryset.annotate(
                    num_student_rationales=num_student_rationales
                )
                .filter(Q(num_student_rationales=0))
                .exclude(questions=question)
            )
        else:
            queryset = queryset.annotate(
                num_student_rationales=num_student_rationales
            ).filter(Q(num_student_rationales=0))

        # Add queryset to form object to keep logic in one spot
        self.queryset = queryset

        self.fields["assignments"] = forms.ModelMultipleChoiceField(
            queryset=queryset,
            required=False,
            label=_("Assignments"),
            help_text=_(
                "Optional. Select assignments to add this question. You can "
                "select multiple assignments. Assignments that this question "
                "is already a part of will not appear in list."
            ),
        )


class TeacherAssignmentsForm(forms.Form):
    """Simple form to help update teacher assignments"""

    assignment = forms.ModelChoiceField(queryset=Assignment.objects.all())


class TeacherGroupsForm(forms.Form):
    """Simple form to help update teacher groups"""

    group = forms.ModelChoiceField(queryset=StudentGroup.objects.all())


class TeacherBlinksForm(forms.Form):
    """Simple form to help update teacher blinks"""

    blink = forms.ModelChoiceField(queryset=BlinkQuestion.objects.all())


class CreateBlinkForm(forms.Form):
    """Simple form to help create blink for teacher"""

    new_blink = forms.ModelChoiceField(queryset=Question.objects.all())


class BlinkSetTimeForm(forms.Form):
    """Simple form to set time limit for blink questions"""

    time_limit = forms.IntegerField(
        max_value=120,
        min_value=15,
        initial=45,
        help_text=_("Set the time limit to be used for each question."),
    )


class BlinkAnswerForm(forms.Form):
    """Form to select one of the answer choices."""

    error_css_class = "validation-error"

    first_answer_choice = forms.ChoiceField(
        label=_("Choose one of these answers:"), widget=forms.RadioSelect
    )

    def __init__(self, answer_choices, *args, **kwargs):
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
        self.base_fields["first_answer_choice"].choices = enumerate(
            choice_texts, 1
        )
        forms.Form.__init__(self, *args, **kwargs)


class BlinkQuestionStateForm(ModelForm):
    """Form to set active state of a BlinkQuestion."""

    class Meta:
        model = BlinkQuestion
        fields = ["active"]


class RankBlinkForm(forms.Form):
    """
    Form to handle reordering or deletion of blinkquestions in a
    blinkassignment.
    """

    # Might be better to set the queryset to limit to teacher's blink set
    q = forms.ModelMultipleChoiceField(
        queryset=BlinkAssignmentQuestion.objects.all(),
        to_field_name="blinkquestion_id",
    )
    rank = forms.CharField(max_length=5, widget=forms.HiddenInput)


class AddBlinkForm(forms.Form):
    """Form to add a blinkquestion to a blinkassignment."""

    # Might be better to set the queryset to limit to teacher's blinks
    blink = forms.ModelChoiceField(queryset=BlinkQuestion.objects.all())


class SignUpForm(ModelForm):
    """Form to register a new user (teacher) with e-mail address.

    The clean method is overridden to add basic password validation."""

    email = forms.CharField(label=_("Email address"))
    username = forms.CharField(label=_("Username"))

    url = forms.URLField(
        label=_("Website"),
        initial="http://",
        max_length=200,
        help_text=_(
            "Please provide an institutional url listing yourself as a "
            "faculty member and showing your e-mail address."
        ),
    )

    class Meta:
        model = User
        fields = ["email", "username"]


class ActivateForm(forms.Form):
    """Form to activate a User and initialize as Teacher, if indicated."""

    is_teacher = forms.BooleanField(required=False)
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=False)
    )


class EmailForm(forms.Form):
    """Form for user email address"""

    email = forms.EmailField()


class AddRemoveQuestionForm(forms.Form):
    q = forms.ModelChoiceField(queryset=Question.objects.all())


class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ["title"]


class DisciplineSelectForm(forms.Form):
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(),
        help_text=_(
            "Optional. Select the discipline to which this item should "
            "be associated."
        ),
    )


class DisciplinesSelectForm(forms.Form):
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.all()
    )


class CategorySelectForm(forms.Form):
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        help_text=_(
            "Type to search and select at least one category for this "
            "question. You can select multiple categories."
        ),
    )


class ReportSelectForm(forms.Form):

    student_groups = forms.ModelMultipleChoiceField(
        label=_("Choose which groups to include in report:"),
        widget=forms.CheckboxSelectMultiple,
        queryset=StudentGroup.objects.none(),
    )

    assignments = forms.ModelMultipleChoiceField(
        label=_("Choose which assignments to include in report:"),
        widget=forms.CheckboxSelectMultiple,
        queryset=Assignment.objects.none(),
    )

    def __init__(self, teacher_username, *args, **kwargs):
        self.base_fields["assignments"].queryset = Teacher.objects.get(
            user__username=teacher_username
        ).assignments.all()
        self.base_fields["student_groups"].queryset = Teacher.objects.get(
            user__username=teacher_username
        ).current_groups.all()
        forms.Form.__init__(self, *args, **kwargs)


class AnswerChoiceForm(forms.ModelForm):
    template_name = "peerinst/question/answer_choice_form.html"

    def clean_text(self):
        if self.cleaned_data["text"].startswith("<p>"):
            return "<br>".join(
                re.findall(r"(?<=<p>)(.+)(?=</p>)", self.cleaned_data["text"])
            )
        else:
            return self.cleaned_data["text"]


def current_year():
    return date.today().year


def year_choices():
    return [(i, i) for i in range(2015, current_year() + 2)]


class StudentGroupCreateForm(forms.ModelForm):
    """Simple form to create a new group"""

    year = forms.TypedChoiceField(
        coerce=int, choices=year_choices, initial=current_year
    )

    class Meta:
        model = StudentGroup
        fields = ["title", "name", "year", "semester"]


class StudentGroupAssignmentForm(ModelForm):
    group = forms.ModelChoiceField(
        queryset=StudentGroup.objects.all(), empty_label=None
    )

    class Meta:
        model = StudentGroupAssignment
        fields = ("group", "due_date", "show_correct_answers")


class StudentGroupAssignmentManagementForm(forms.Form):
    group_assignment = forms.ModelChoiceField(
        queryset=StudentGroupAssignment.objects.all()
    )
