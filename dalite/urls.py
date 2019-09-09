# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin

import views
from peerinst import views as peerinst_views

admin.site.site_header = admin.site.site_title = _("Dalite NG administration")

# LTI
urlpatterns = [url(r"^lti/", include("django_lti_tool_provider.urls"))]

# Apps
urlpatterns += i18n_patterns(
    url(r"^reputation/", include("reputation.urls", namespace="reputation")),
    url(r"^quality/", include("quality.urls", namespace="quality")),
    url(r"^tos/", include("tos.urls")),
    url(r"", include("peerinst.urls")),
    url(r"^forums/", include("pinax.forums.urls", namespace="pinax_forums")),
    url(
        r"^assignment/(?P<assignment_id>[^/]+)/",
        include(
            [
                # Question table of contents for assignment - Enforce
                # sameorigin to prevent access from LMS
                url(
                    r"^$",
                    xframe_options_sameorigin(
                        peerinst_views.QuestionListView.as_view()
                    ),
                    name="question-list",
                ),
                url(
                    r"(?P<question_id>\d+)/",
                    include(
                        [
                            # Dalite question
                            url(
                                r"^$", peerinst_views.question, name="question"
                            ),
                            # Question reset (for testing purposes) - Enforce
                            # sameorigin to prevent access from LMS
                            url(
                                r"^reset/$",
                                peerinst_views.reset_question,
                                name="reset-question",
                            ),
                        ]
                    ),
                ),
                url(
                    r"^update/$",
                    peerinst_views.AssignmentUpdateView.as_view(),
                    name="assignment-update",
                ),
            ]
        ),
    ),
    url(r"^grappelli/", include("grappelli.urls")),
    url(
        r"admin_index_wrapper/",
        views.admin_index_wrapper,
        name="admin_index_wrapper",
    ),
    url(r"^admin/", include(admin.site.urls)),
)

# Set language view
urlpatterns += [url(r"^i18n/", include("django.conf.urls.i18n"))]

# Media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Errors
#  handler400 = views.errors.response_400
#  handler403 = views.errors.response_403
handler404 = "dalite.views.errors.response_404"
#  handler500 = "dalite.views.errors.response_500"
