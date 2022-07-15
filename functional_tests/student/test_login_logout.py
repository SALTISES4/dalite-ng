import re
import time

from django.urls import reverse
from selenium.webdriver.common.keys import Keys

from functional_tests.fixtures import *  # noqa
from peerinst.students import (
    create_student_token,
    get_student_username_and_password,
)


def signin(browser, student, mail_outbox, new=False):
    email = student.student.email

    browser.get("{}{}".format(browser.server_url, reverse("login")))

    login_link = browser.find_element_by_link_text("LOGIN")
    login_link.click()

    input_ = browser.find_element_by_name("email")
    input_.clear()
    input_.send_keys(email)
    input_.send_keys(Keys.ENTER)

    assert len(mail_outbox) == 1
    assert list(mail_outbox[0].to) == [email]

    m = re.search(
        r"http[s]*://.*/student/\?token=.*", mail_outbox[0].body
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

    assert browser.current_url == browser.server_url + "/en/login/"


def consent_to_tos(browser):
    browser.find_element_by_id("tos-accept").click()

    sharing = browser.find_element_by_id("student-tos-sharing--sharing")
    assert sharing.text == "Sharing"


def test_fake_link(browser):
    email = "test@test.com"
    username, _ = get_student_username_and_password(email)
    token = create_student_token(username, email)

    signin_link = "{}{}?token={}".format(
        browser.server_url, reverse("student-page"), token
    )

    browser.get(signin_link)

    assert re.search(r"student/", browser.current_url)

    err = (
        "There is no user corresponding to the given link. "
        "You may try asking for another one."
    )
    browser.find_element_by_xpath(f"//*[contains(text(), '{err}')]")


def test_student_login_logout(browser, assert_, mail_outbox, student):
    signin(browser, student, mail_outbox, new=False)
    access_logged_in_account_from_landing_page(browser, student)
    logout(browser, assert_)


def test_new_student_login(browser, student_new, mail_outbox):
    signin(browser, student_new, mail_outbox, new=True)
    consent_to_tos(browser)
