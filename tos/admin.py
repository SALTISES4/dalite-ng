from django.contrib import admin

from . import models

admin.register(models.Tos)
admin.register(models.Consent)


@admin.register(models.Tos)
class TosAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Consent)
class ConsentAdmin(admin.ModelAdmin):
    pass
