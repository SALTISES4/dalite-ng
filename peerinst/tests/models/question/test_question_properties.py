from peerinst.tests.fixtures import *  # noqa


def test_get_all_student_answers(answers, teachers):
    question = answers[0].question
    answer_set = question.answer_set.all()
    owner = teachers[0]
    collaborator = teachers[1]

    # Prep data
    for answer in answer_set:
        assert answer.user_token
        assert answer.user_token != owner.user.username
        assert answer.user_token != collaborator.user.username
    assert question.get_all_student_answers().count() == len(answer_set)
    assert answer_set[0] in question.get_all_student_answers().all()
    assert answer_set[1] in question.get_all_student_answers().all()

    # Attach owner to question
    question.user = owner.user
    question.save()

    # Attach owner to answer
    answer_set[0].user_token = owner.user.username
    answer_set[0].save()

    assert question.get_all_student_answers().count() == len(answer_set) - 1
    assert answer_set[0] not in question.get_all_student_answers().all()

    # Attach collaborator to question
    question.collaborators.add(collaborator.user)

    # Attach collaborator to answer
    answer_set[1].user_token = collaborator.user.username
    answer_set[1].save()

    assert question.get_all_student_answers().count() == len(answer_set) - 2
    assert answer_set[1] not in question.get_all_student_answers().all()
