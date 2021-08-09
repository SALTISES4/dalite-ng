from django.urls import reverse

from peerinst.models import Question, QuestionFlag, QuestionFlagReason
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


def test_fix_question_view(client, teacher, question, student):
    # Make a fully invalid question
    qs = Question.objects.filter(pk=question.pk)
    # make flag object, and attach question
    flag = QuestionFlag.objects.create(
        question=question, user=teacher.user, flag=True
    )
    # create reason for flagging question
    flag_reason, _ = QuestionFlagReason.objects.get_or_create(
        title=QuestionFlagReason.CHOICES[0][0]
    )
    message = str(QuestionFlagReason.CHOICES[0][1])
    # attach reason to flag object
    flag.flag_reason.add(flag_reason)
    flag.save()

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

    # 4. If flagged, nothing can be done, but give reason and offer clone
    response = client.get(url)
    assert response.status_code == 200

    # 5. If missing answer choices, check ownership, check is_editable and
    # then provide link to add
    flag.delete()
    response = client.get(url)
    assert response.status_code == 200

    # assert "you cannot fix this problem, but you can make an editable copy"
    # question, remove
    # old question from teacher list, add new and redirect"

    question.owner = teacher.user
    question.save()

    response = client.get(url)
    assert response.status_code == 200

    # assert button to answerchoice create in page

    # 6. If only missing sample answers, anyone can add them
