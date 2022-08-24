from django.urls import reverse


def test_lti_middleware(client, student, assignment):
    response = client.get("/en/")
    assert response.status_code == 200

    # Login student and set LTI session variable
    client.force_login(student.student, "peerinst.lti.LTIBackendStudentsOnly")

    # - Can access general pages, like landing page
    response = client.get(reverse("landing_page"))
    assert response.status_code == 200

    # - Can access lti question view, student-page-LTI
    response = client.get(
        reverse(
            "question", args=(assignment.pk, assignment.questions.first().pk)
        ),
        follow=True,
    )
    assert response.status_code == 200

    response = client.get(reverse("student-page-LTI"), follow=True)
    assert response.status_code == 200

    # - Can't access non-LTI student views
    response = client.get(reverse("student-page"), follow=True)
    assert response.status_code == 403

    client.force_login(student.student, "peerinst.lti.LTIBackendStudentsOnly")

    response = client.get(reverse("welcome"), follow=True)
    assert response.status_code == 403
