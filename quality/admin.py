from django.contrib import admin

from . import models

admin.site.register(models.LikelihoodCriterion)
admin.site.register(models.LikelihoodCriterionRules)
admin.site.register(models.MinCharsCriterion)
admin.site.register(models.MinCharsCriterionRules)
admin.site.register(models.MinWordsCriterion)
admin.site.register(models.MinWordsCriterionRules)
admin.site.register(models.NegWordsCriterion)
admin.site.register(models.NegWordsCriterionRules)
admin.site.register(models.Quality)
admin.site.register(models.RightAnswerCriterion)
admin.site.register(models.RightAnswerCriterionRules)
admin.site.register(models.SelectedAnswerCriterion)
admin.site.register(models.SelectedAnswerCriterionRules)
admin.site.register(models.UsesCriterion)
