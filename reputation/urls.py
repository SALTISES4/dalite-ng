# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views


def reputation_patterns():
    return [
        url(r"^reputation/$", views.reputation.reputation, name="reputation")
    ]


urlpatterns = sum([reputation_patterns()], [])
