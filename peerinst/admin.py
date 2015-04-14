# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import exceptions
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from . import models

class AnswerChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        forms = [
            f for f in self.forms
            if getattr(f, 'cleaned_data', None) and not f.cleaned_data.get('DELETE', False)
        ]
        errors = []
        if len(forms) < 2:
            errors.append(_('There must be at least two answer choices.'))
        correct_answers = sum(f.cleaned_data.get('correct', False) for f in forms)
        if not correct_answers:
            errors.append(_('At least one of the answers must be marked as correct.'))
        if errors:
            raise exceptions.ValidationError(errors)

class AnswerChoiceInline(admin.TabularInline):
    model = models.AnswerChoice
    formset = AnswerChoiceInlineFormSet
    max_num = 5
    extra = 5
    ordering = ['id']

class AnswerModelForm(forms.ModelForm):
    class Meta:
        labels = {'first_answer_choice': _('Associated answer')}
        help_texts = {
            'rationale':
                _('An example rationale that will be shown to students during the answer review.'),
            'first_answer_choice':
                _('The number of the associated answer; 1 = first answer, 2 = second answer etc.'),
        }

class AnswerInline(admin.StackedInline):
    model = models.Answer
    form = AnswerModelForm
    verbose_name = _('example answer')
    verbose_name_plural = _('example answers')
    extra = 0
    fields = ['rationale', 'first_answer_choice']
    inline_classes = ['grp-collapse', 'grp-open']

    def get_queryset(self, request):
        # Only include example answers not belonging to any student
        qs = admin.StackedInline.get_queryset(self, request)
        return qs.filter(user_token='', show_to_others=True)

@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'text']}),
        (_('Main image or video'), {'fields': ['primary_image', 'primary_video_url']}),
        (_('Secondary image or video'), {
            'fields': ['secondary_image', 'secondary_video_url'],
            'classes': ['grp-collapse', 'grp-closed'],
            'description': _(
                'Choose either a video or image to include on the first page of the question, '
                'where students select concept tags. This is only used if you want the question '
                'to be hidden when students select concept tags; instead, a preliminary video or '
                'image can be displayed. The main question image will be displayed on all '
                'subsequent pages.'
            ),
        }),
        (None, {'fields': ['answer_style']}),
    ]
    radio_fields = {'answer_style': admin.HORIZONTAL}
    inlines = [AnswerChoiceInline, AnswerInline]

    def save_related(self, request, form, formsets, change):
        for fs in formsets:
            if fs.model is models.Answer:
                answers = fs.save(commit=False)
                for a in answers:
                    a.show_to_others = True
                    a.save()
                fs.save_m2m()
            else:
                fs.save()

@admin.register(models.Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['questions']
    class Media:
        js = ['peerinst/js/prepopulate_added_question.js']
