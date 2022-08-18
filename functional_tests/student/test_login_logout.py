import re
import time

from django.urls import reverse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa
from peerinst.students import (
    create_student_token,
    get_student_username_and_password,
)

TIMEOUT = 30


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

    try:
        WebDriverWait(browser, timeout=TIMEOUT).until(
            lambda d: len(mail_outbox) == 1
        )
    except TimeoutException:
        assert False
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


def test_fake_link(browser):
    email = "test@test.com"
    username, _ = get_student_username_and_password(email)
    token = create_student_token(username, email)

    signin_link = (
        f'{browser.server_url}{reverse("student-page")}?token={token}'
    )

    browser.get(signin_link)

    assert re.search(r"student/", browser.current_url)

    err = (
        "There is no user corresponding to the given link. "
        "You may try asking for another one."
    )
    browser.find_element_by_xpath(f"//*[contains(text(), '{err}')]")


def test_students_cannot_access_password_change(browser, mail_outbox, student):
    signin(browser, student, mail_outbox, new=False)
    browser.get(f'{browser.server_url}{reverse("password_change")}')

    # user_passes_test redirects to login which should redirect to account
    assert browser.current_url.endswith("student/")


def test_students_cannot_reset_password(browser, mail_outbox, student):
    browser.get(f'{browser.server_url}{reverse("password_reset")}')

    browser.find_element(By.ID, "id_email").send_keys(student.student.email)
    browser.find_element(By.ID, "submit-btn").click()

    time.sleep(5)
    assert len(mail_outbox) == 0
    assert (
        "If you have a non-student account that is active, you will receive an email with instructions for setting a new password."  # noqa
        in browser.page_source
    )


def test_student_cannot_login_via_username_and_password(browser, student):
    browser.get(f'{browser.server_url}{reverse("login")}')
    browser.find_element_by_xpath(
        "//button[contains(.,'Login via SALTISE')]"
    ).click()

    username = student.student.username
    password = "test"
    student.student.set_password(password)
    student.student.save()

    username_input = browser.find_element_by_xpath(
        "//input[@id='id_username']"
    )
    username_input.clear()
    username_input.send_keys(username)

    password_input = browser.find_element_by_xpath(
        "//input[@id='id_password']"
    )
    password_input.clear()
    password_input.send_keys(password)

    submit_button = browser.find_element_by_xpath(
        "//button[@id='submit-btn']"
    ).click()

    assert browser.current_url.endswith("login/")
    assert (
        "Your username and password didn't match or your account has not yet been activated or you are trying to log in with a student account."  # noqa
        in browser.page_source
    )


def test_student_login_logout(browser, assert_, mail_outbox, student):
    signin(browser, student, mail_outbox, new=False)
    access_logged_in_account_from_landing_page(browser, student)
    logout(browser, assert_)


def test_new_student_login(browser, student_new, mail_outbox):
    signin(browser, student_new, mail_outbox, new=True)
    consent_to_tos(browser)
