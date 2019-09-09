# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from . import models

admin.site.register(models.CommonRationaleChoicesCriterion)
admin.site.register(models.ConvincingRationalesCriterion)
admin.site.register(models.NAnswersCriterion)
admin.site.register(models.NQuestionsCriterion)
admin.site.register(models.QuestionLikedCriterion)
admin.site.register(models.RationaleEvaluationCriterion)
admin.site.register(models.StudentRationaleEvaluationCriterion)
admin.site.register(models.UsesCriterion)
