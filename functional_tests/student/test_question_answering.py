import re
import time

from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from functional_tests.fixtures import *  # noqa
from functional_tests.student.test_index_workflow import join_group_with_link
from faker import Faker
from datetime import datetime, timedelta
import time
from peerinst.models.answer import Answer, AnswerChoice
import pytz


fake = Faker()


def signin(browser, student, mailoutbox, new=False):
    email = student.student.email

    browser.get("{}{}".format(browser.server_url, reverse("login")))

    login_link = browser.find_element_by_link_text("LOGIN")
    login_link.click()

    input_ = browser.find_element_by_name("email")
    input_.clear()
    input_.send_keys(email)
    input_.send_keys(Keys.ENTER)

    assert len(mailoutbox) == 1
    assert list(mailoutbox[0].to) == [email]

    m = re.search(
        "http[s]*://.*/student/\?token=.*", mailoutbox[0].body
    )  # noqa W605
    signin_link = m.group(0)

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
        "Welcome back {}".format(student.student.email)
    )
    link.click()
    assert re.search(r"student/", browser.current_url)


def logout(browser, assert_):
    icon = browser.find_element_by_xpath("//i[contains(text(), 'menu')]")
    icon.click()

    logout_button = browser.find_element_by_link_text("Logout")
    browser.wait_for(assert_(logout_button.is_enabled()))
    # FIXME:
    # Assertion shoud include logout_button.is_displayed() but throws w3c error
    time.sleep(2)
    logout_button.click()

    assert browser.current_url == browser.server_url + "/en/"

    browser.find_element_by_link_text("Login")
    browser.find_element_by_link_text("Signup")


def consent_to_tos(browser):
    browser.find_element_by_id("tos-accept").click()

    sharing = browser.find_element_by_id("student-tos-sharing--sharing")
    assert sharing.text == "Sharing"


def answer_questions(browser, student, assignment):
    browser_url = browser.server_url
    str(browser_url)
    browser.find_element_by_class_name(
        "student-group--assignment-title"
    ).click()
    time.sleep(3)
    url = browser.current_url
    str(url)
    browser.get(browser_url + url[21:])
    first = True
    answers_done = 0
    for question in assignment.questions.all():
        time.sleep(3)
        browser.find_element_by_class_name("mdc-radio__native-control").click()
        rationale = fake.sentence(nb_words=6)
        browser.find_element_by_id("id_rationale").send_keys(rationale)
        browser.find_element_by_class_name("mdc-button").click()
        assert rationale in browser.find_element_by_id("your-rationale").text
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
        assert rationale in browser.find_element_by_id("your-rationale").text
        assert (
            other_rationale
            in browser.find_element_by_id("chosen-rationale").text
        )
        if answers_done == 9:
            browser.find_element_by_class_name("mdc-button").click()
        else:
            if first:
                browser.find_element_by_class_name("md-60").click()
            else:
                browser.find_elements_by_class_name("md-60")[1].click()
        first = False
        answers_done += 1

    assert (
        "You've finished this assignment. You"
        in browser.find_element_by_tag_name("p").text
    )


def test_question_answering(
    browser,
    assert_,
    mailoutbox,
    students,
    group,
    teacher,
    student_group_assignment,
    assignment,
):
    group.teacher.add(teacher)
    group.save()
    student = students[0]
    for question in assignment.questions.all():
        for i in range(0, 4):
            q = AnswerChoice.objects.create(
                question=question,
                text=fake.sentence(nb_words=6),
                correct=False,
            )
            if i == 0:
                q.correct = True
            q.save()
            Answer.objects.create(
                question=question,
                user_token="",
                first_answer_choice=i,
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
    signin(browser, student, mailoutbox)
    join_group_with_link(browser, group)
    answer_questions(browser, student, assignment)
