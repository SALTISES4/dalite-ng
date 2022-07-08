import re

import bleach
from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from blink.models import BlinkAssignmentQuestion, BlinkQuestion
from peerinst.models import Question
from peerinst.templatetags.bleach_html import ALLOWED_TAGS


class AddBlinkForm(forms.Form):
    """Form to add a blinkquestion to a blinkassignment."""

    # Might be better to set the queryset to limit to teacher's blinks
    blink = forms.ModelChoiceField(queryset=BlinkQuestion.objects.all())


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
                            re.split(
                                r"<br(?: /)?>",
                                bleach.clean(
                                    pair[1],
                                    tags=ALLOWED_TAGS,
                                    styles=[],
                                    strip=True,
                                ),
                            )
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


class BlinkSetTimeForm(forms.Form):
    """Simple form to set time limit for blink questions"""

    time_limit = forms.IntegerField(
        max_value=120,
        min_value=15,
        initial=45,
        help_text=_("Set the time limit to be used for each question."),
    )


class CreateBlinkForm(forms.Form):
    """Simple form to help create blink for teacher"""

    new_blink = forms.ModelChoiceField(queryset=Question.objects.all())


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
