import json
from unittest import mock

from django.template.response import TemplateResponse
from django.urls import reverse

from peerinst.tests.fixtures import *  # noqa
from quality.models import Quality, QualityType, QualityUseType, UsesCriterion
from quality.tests.fixtures import *  # noqa
from quality.views.edit import (
    verify_assignment,
    verify_group,
    verify_question,
    verify_teacher,
)


def test_verify_question(client, rf, question, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    resp = verify_question(req, "validation", question.pk)

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_verify_assignment(client, rf, student_group_assignment, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    student_group_assignment.group.teacher.add(teacher)

    resp = verify_assignment(req, "validation", student_group_assignment.pk)

    assert isinstance(resp, Quality)


def test_verify_assignment__assignment_doesnt_exist(client, rf):
    req = rf.get("/test")

    resp = verify_assignment(req, "validation", 0)

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_verify_assignment__teacher_doesnt_exist(
    client, rf, student_group_assignment, user
):
    req = rf.get("/test")
    req.user = user

    resp = verify_assignment(req, "validation", student_group_assignment.pk)

    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_verify_assignment__teacher_doesnt_have_access(
    client, rf, student_group_assignment, teacher
):
    req = rf.get("/test")
    req.user = teacher.user

    student_group_assignment.group.teacher.remove(teacher)

    resp = verify_assignment(req, "validation", student_group_assignment.pk)

    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_verify_assignment__use_type_doesnt_exist(
    client, rf, student_group_assignment, teacher
):
    req = rf.get("/test")
    req.user = teacher.user

    student_group_assignment.group.teacher.add(teacher)

    resp = verify_assignment(req, "fake", student_group_assignment.pk)

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_verify_group(client, rf, group, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    group.teacher.add(teacher)

    resp = verify_group(req, "validation", group.pk)

    assert isinstance(resp, Quality)


def test_verify_group__group_doesnt_exist(client, rf):
    req = rf.get("/test")

    resp = verify_group(req, "validation", 0)

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_verify_group__teacher_doesnt_exist(client, rf, group, user):
    req = rf.get("/test")
    req.user = user

    resp = verify_group(req, "validation", group.pk)

    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_verify_group__teacher_doesnt_have_access(client, rf, group, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    group.teacher.remove(teacher)

    resp = verify_group(req, "validation", group.pk)

    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_verify_group__use_type_doesnt_exist(client, rf, group, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    group.teacher.add(teacher)

    resp = verify_group(req, "fake", group.pk)

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_verify_teacher(client, rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    resp = verify_teacher(req, "validation")

    assert isinstance(resp, Quality)


def test_verify_teacher__teacher_doesnt_exist(client, rf):
    req = rf.get("/test")

    resp = verify_teacher(req, "validation")

    assert resp.status_code == 403
    assert resp.template_name == "403.html"


def test_verify_teacher__use_type_doesnt_exist(client, rf, teacher):
    req = rf.get("/test")
    req.user = teacher.user

    resp = verify_teacher(req, "fake")

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_index__question(client, question, teacher):
    client.login(username=teacher.user.username, password="test")
    resp = client.get(
        f"/quality/edit/?type=validation&question={question.pk}",
        follow=True,
    )
    #  assert resp.status_code == 200
    #  assert any(t.name == "quality/edit/index.html" for t in resp.templates)
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_index__assignment(client, student_group_assignment, teacher):
    student_group_assignment.group.teacher.add(teacher)

    client.login(username=teacher.user.username, password="test")
    resp = client.get(
        "/quality/edit/?type=validation&assignment={}".format(
            student_group_assignment.pk
        ),
        follow=True,
    )
    assert resp.status_code == 200
    assert any(t.name == "quality/edit/index.html" for t in resp.templates)


def test_index__group(client, group, teacher):
    group.teacher.add(teacher)

    client.login(username=teacher.user.username, password="test")
    resp = client.get(
        f"/quality/edit/?type=validation&teacher={group.pk}",
        follow=True,
    )
    assert resp.status_code == 200
    assert any(t.name == "quality/edit/index.html" for t in resp.templates)


def test_index__teacher(client, teacher):
    client.login(username=teacher.user.username, password="test")
    resp = client.get(
        f"/quality/edit/?type=validation&teacher={teacher.pk}",
        follow=True,
    )
    assert resp.status_code == 200
    assert any(t.name == "quality/edit/index.html" for t in resp.templates)


def test_index__missing_pk(client, student_group_assignment, teacher):
    client.login(username=teacher.user.username, password="test")
    resp = client.get("/quality/edit/?type=validation", follow=True)
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_index__missing_type(client, student_group_assignment, teacher):
    client.login(username=teacher.user.username, password="test")
    resp = client.get(
        f"/quality/edit/?assignment={student_group_assignment.pk}",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_index__question_error(client, rf, question, teacher):
    client.login(username=teacher.user.username, password="test")
    with mock.patch("quality.views.edit.verify_question") as verify_question:
        req = rf.get("/test")
        verify_question.return_value = TemplateResponse(
            req, "400.html", status=400
        )
        resp = client.get(
            f"/quality/edit/?type=validation&question={question.pk}",
            follow=True,
        )
        assert resp.status_code == 400
        assert resp.template_name == "400.html"


def test_index__assignment_error(
    client, rf, student_group_assignment, teacher
):
    client.login(username=teacher.user.username, password="test")
    with mock.patch(
        "quality.views.edit.verify_assignment"
    ) as verify_assignment:
        req = rf.get("/test")
        verify_assignment.return_value = TemplateResponse(
            req, "400.html", status=400
        )
        resp = client.get(
            "/quality/edit/?type=validation&assignment={}".format(
                student_group_assignment.pk
            ),
            follow=True,
        )
        assert resp.status_code == 400
        assert resp.template_name == "400.html"


def test_index__group_error(client, rf, group, teacher):
    client.login(username=teacher.user.username, password="test")
    with mock.patch("quality.views.edit.verify_group") as verify_group:
        req = rf.get("/test")
        verify_group.return_value = TemplateResponse(
            req, "400.html", status=400
        )
        resp = client.get(
            f"/quality/edit/?type=validation&group={group.pk}",
            follow=True,
        )
        assert resp.status_code == 400
        assert resp.template_name == "400.html"


def test_index__teacher_error(client, rf, teacher):
    client.login(username=teacher.user.username, password="test")
    with mock.patch("quality.views.edit.verify_teacher") as verify_teacher:
        req = rf.get("/test")
        verify_teacher.return_value = TemplateResponse(
            req, "400.html", status=400
        )
        resp = client.get(
            f"/quality/edit/?type=validation&teacher={teacher.pk}",
            follow=True,
        )
        assert resp.status_code == 400
        assert resp.template_name == "400.html"


def test_add_criterion(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:add-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": min_words_criterion.name,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 200


def test_add_criterion__wrong_type(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:add-criterion"),
        "random string",
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_add_criterion__missing_params(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:add-criterion"),
        json.dumps({"quality": student_group_assignment.quality.pk}),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"

    resp = client.post(
        reverse("quality:add-criterion"),
        json.dumps({"criterion": min_words_criterion.name}),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_add_criterion__wrong_quality_pk(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:add-criterion"),
        json.dumps({"quality": -1, "criterion": min_words_criterion.name}),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_add_criterion__wrong_criterion_name(
    client, student_group_assignment, teacher
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:add-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": "fake",
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_update_criterion(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": min_words_criterion.name,
                "field": "weight",
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 200


def test_update_criterion__wrong_type(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:update-criterion"),
        "random string",
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_update_criterion__missing_params(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "criterion": min_words_criterion.name,
                "field": "weight",
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "field": "weight",
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": min_words_criterion.name,
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": min_words_criterion.name,
                "field": "weight",
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_update_criterion__wrong_quality_pk(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": -1,
                "criterion": min_words_criterion.name,
                "field": "weight",
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_update_criterion__wrong_criterion(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": "fake",
                "field": "weight",
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_update_criterion__wrong_field(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:update-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": min_words_criterion.name,
                "field": "fake",
                "value": 2,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_remove_criterion(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:remove-criterion"),
        json.dumps(
            {
                "quality": student_group_assignment.quality.pk,
                "criterion": min_words_criterion.name,
            }
        ),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 200


def test_remove_criterion__wrong_type(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:remove-criterion"),
        "random string",
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_remove_criterion__missing_params(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:remove-criterion"),
        json.dumps({"criterion": min_words_criterion.name}),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"

    resp = client.post(
        reverse("quality:remove-criterion"),
        json.dumps({"quality": student_group_assignment.quality.pk}),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_remove_criterion__wrong_quality_key(
    client,
    student_group_assignment,
    teacher,
    min_words_criterion,
    min_words_rules,
):
    quality_type = QualityType.objects.get(type="studentgroupassignment")
    quality_use_type = QualityUseType.objects.get(type="validation")
    student_group_assignment.quality = Quality.objects.create(
        quality_type=quality_type, quality_use_type=quality_use_type
    )
    student_group_assignment.save()
    student_group_assignment.group.teacher.add(teacher)
    UsesCriterion.objects.create(
        quality=student_group_assignment.quality,
        name=min_words_criterion.name,
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=0,
    )
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("quality:remove-criterion"),
        json.dumps({"quality": -1, "criterion": min_words_criterion.name}),
        content_type="application/json",
        follow=True,
    )
    assert resp.status_code == 400
    assert resp.template_name == "400.html"
