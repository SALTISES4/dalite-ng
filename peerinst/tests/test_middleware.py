from django.urls import reverse

from peerinst.tests.fixtures.student import login_student


def test_lti_login(client, student, assignment):
    response = client.get("/en/")
    assert response.status_code == 200

    # Login student and set LTI session variable
    assert login_student(client, student)
    session = client.session
    session["LTI"] = True
    session.save()

    # - Can access general pages, like landing page
    response = client.get(reverse("landing_page"))
    assert response.status_code == 200

    # - Can access lti question view
    response = client.get(
        reverse(
            "question", args=(assignment.pk, assignment.questions.first().pk)
        )
    )
    assert response.status_code == 200

    # - Can't access non-LTI student views
    response = client.get(reverse("student-page"))
    assert response.status_code == 403
