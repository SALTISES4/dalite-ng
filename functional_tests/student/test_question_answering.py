import itertools
import re
import time
from datetime import datetime, timedelta

import pytz
from django.urls import reverse
from faker import Faker
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa
from functional_tests.student.test_index_workflow import join_group_with_link
from peerinst.models.answer import Answer, AnswerChoice

fake = Faker()


def signin(browser, student, mail_outbox, new=False):
    email = student.student.email

    browser.get(f'{browser.server_url}{reverse("login")}')

    browser.find_element_by_xpath(
        "//button[contains(.,'Login via email')]"
    ).click()

    input_ = browser.find_element_by_name("email")
    input_.clear()
    input_.send_keys(email)
    input_.send_keys(Keys.ENTER)

    assert len(mail_outbox) == 1
    assert list(mail_outbox[0].to) == [email]

    m = re.search(
        r"http[s]*://.*/student/\?token=.*", mail_outbox[0].body
    )  # noqa W605
    signin_link = m[0]

    browser.get(signin_link)

    if new:
        assert re.search(
            r"/(\w{2})/tos/tos/student/\?next=/\1/student/",
            browser.current_url,
        )
    else:
        assert re.search(r"/en/student/\?token=", browser.current_url)


def access_logged_in_account_from_landing_page(browser, student):
    browser.get(browser.server_url)
    link = browser.find_element_by_link_text(
        f"Welcome back, {student.student.email}"
    )
    link.click()
    assert re.search(r"student/", browser.current_url)


def logout(browser, assert_):
    icon = browser.find_element_by_xpath("//i[contains(text(), 'menu')]")
    icon.click()

    logout_button = browser.find_element_by_id("logout")
    browser.wait_for(assert_(logout_button.is_enabled()))
    # FIXME:
    # Assertion shoud include logout_button.is_displayed() but throws w3c error
    time.sleep(2)
    logout_button.click()

    assert browser.current_url == f"{browser.server_url}/en/login/"


def consent_to_tos(browser):
    browser.find_element_by_id("tos-accept").click()

    sharing = browser.find_element_by_id("student-tos-sharing--sharing")
    assert sharing.text == "Sharing"


def answer_questions(browser, student, assignment):
    browser_url = browser.server_url
    browser.find_element_by_class_name(
        "student-group--assignment-link"
    ).click()

    first = True
    for answers_done, question in enumerate(assignment.questions.all()):
        time.sleep(3)
        browser.find_element_by_class_name("mdc-radio__native-control").click()
        rationale = "This is a rationale that will pass all validators"
        tinymce_embed = browser.find_element_by_tag_name("iframe")
        browser.switch_to.frame(tinymce_embed)
        ifrinputbox = browser.find_element_by_id("tinymce")
        ifrinputbox.send_keys(rationale)
        browser.switch_to.default_content()
        browser.find_element_by_class_name("mdc-button").click()

        browser.wait_for(
            lambda: assert_(
                rationale in browser.find_element_by_id("your-rationale").text
            )
        )
        other_rationale = browser.find_element_by_class_name(
            "mdc-form-field"
        ).text
        browser.find_element_by_class_name("mdc-radio__native-control").click()
        try:
            button = WebDriverWait(browser, 30).until(
                EC.element_to_be_clickable((By.ID, "answer-form"))
            )
        except TimeoutException:
            assert False
        button.click()
        browser.wait_for(
            lambda: assert_(
                rationale in browser.find_element_by_id("your-rationale").text
            )
        )
        browser.wait_for(
            lambda: assert_(
                other_rationale
                in browser.find_element_by_id("chosen-rationale").text
            )
        )
        if answers_done == 9:
            finish_button = WebDriverWait(browser, timeout=10).until(
                EC.element_to_be_clickable((By.ID, "finish-button"))
            )
            finish_button.click()

            try:
                WebDriverWait(browser, timeout=10).until(EC.alert_is_present())
            except TimeoutException:
                assert False
            alert = browser.switch_to.alert

            assert (
                "Once you click OK you will not be able to complete any unanswered questions."  # noqa E501
                in alert.text
            )

            alert.accept()
        elif first:
            browser.find_element_by_class_name("md-60").click()
        else:
            browser.find_elements_by_class_name("md-60")[1].click()
        first = False
    assert (
        "You've finished this assignment. You"
        in browser.find_element_by_tag_name("p").text
    )


def test_question_answering(
    browser,
    assert_,
    mail_outbox,
    students,
    group,
    teacher,
    student_group_assignment,
    assignment,
):
    group.teacher.add(teacher)
    group.save()
    student = students[0]
    for question, i in itertools.product(assignment.questions.all(), range(4)):
        q = AnswerChoice.objects.create(
            question=question,
            text=fake.paragraph(),
            correct=False,
        )
        if i == 0:
            q.correct = True
        q.save()
        for _ in range(4):
            Answer.objects.create(
                question=question,
                user_token="",
                first_answer_choice=i,
                rationale=fake.sentence(nb_words=10),
                datetime_start=datetime.now(pytz.utc),
                datetime_first=datetime.now(pytz.utc),
                datetime_second=datetime.now(pytz.utc),
            )
    assignment.save()
    student_group_assignment.assignment = assignment
    student_group_assignment.group = group
    student_group_assignment.distribution_date = datetime.now(pytz.utc)
    student_group_assignment.due_date = datetime.now(pytz.utc) + timedelta(
        days=30
    )
    student_group_assignment.save()
    signin(browser, student, mail_outbox)
    join_group_with_link(browser, group)
    answer_questions(browser, student, assignment)
