from django.core.urlresolvers import reverse

from tos.models import Role, Tos

from .views.test_views import QuestionViewTestCase


class TOSError(QuestionViewTestCase):
    def test_no_tos_exists(self):
        # Delete TOS
        tos = Tos.objects.all().first()
        tos.delete()
        response = self.question_get()
        # This will raise error in tos models.py as no TOS exists and we want
        # custom error page to be rendered with message from app
        self.assertTemplateUsed(response, "500.html")
        self.assertContains(
            response, "There is no terms of service yet.", status_code=500
        )

        # create role
        role = Role.objects.get(role="student")

        # Add TOS
        new_TOS = Tos(version=1, text="Test", current=True, role=role)
        new_TOS.save()
        response = self.question_get()
        self.assertRedirects(
            response,
            reverse("tos:tos_consent", kwargs={"role": "student"})
            + "?next="
            + self.question_url,
            status_code=302,
            target_status_code=200,
        )
