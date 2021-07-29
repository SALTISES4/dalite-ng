from django.urls import reverse
from django.utils.translation import gettext as _

from peerinst.models import Question, QuestionFlag
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


def test_fix_question_view(client, teacher, question, student):
    # Make a fully invalid question
    qs = Question.objects.filter(pk=question.pk)
    flag = QuestionFlag.objects.create(
        question=question,
        user=teacher.user,
    )
    assert Question.is_flagged(qs)
    assert Question.is_missing_answer_choices(qs)
    assert Question.is_missing_sample_answers(qs)

    url = reverse("question-fix", args=(question.pk,))

    # 1. Require authentication
    response = client.get(url)
    assert response.status_code == 302
    assert "login" in response.url

    # 2. Require teacher
    assert login_student(client, student)

    response = client.get(url)
    assert response.status_code == 302
    assert "access_denied_and_logout" in response.url

    # 3. Require GET
    assert login_teacher(client, teacher)

    response = client.post(url, {})
    assert response.status_code == 405

    # 4. If flagged, nothing can be done but state why and offer to create
    # new question
    response = client.get(url)
    assert response.status_code == 200

    message = _(
        "This question has been flagged for copyright infringement.  Flags \
        are reviewed by SALTISE and removed once question is corrected.  To \
        create a new question that resolves the flagged issue, use the link \
        below."
    )

    assert " ".join(message.split()) in response.content.decode()

    link = 'href="/en/question/create"'

    assert link in response.content.decode()

    # 5. If missing answer choices, check ownership and then provide link
    # to add
    flag.delete()
    response = client.get(url)
    assert response.status_code == 200

    # assert "you cannot fix this problem, but you can copy question, remove
    # old question from teacher list, add new and redirect"

    question.owner = teacher.user
    question.save()

    response = client.get(url)
    assert response.status_code == 200

    # assert button to answerchoice create in page

    # 6. If only missing sample answers, anyone can add them

    # 7. If is_valid, say so
