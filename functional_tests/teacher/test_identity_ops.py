import re
import time

from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from functional_tests.fixtures import *  # noqa

from .utils import accept_cookies, go_to_account, login, logout


def start(browser, teacher):
    login(browser, teacher)
    accept_cookies(browser)
    go_to_account(browser)
    browser.find_element_by_id("identity-section").click()


def test_change_password(browser, assert_, teacher):
    start(browser, teacher)
    browser.find_element_by_id("edit-user-btn").click()

    # Check content
    assert (
        "Back to My Account"
        in browser.find_element_by_class_name("admin-link").text
    )
    assert "Password change" in browser.find_element_by_tag_name("h2").text

    # Check breadcrumbs
    browser.find_element_by_link_text("Back to My Account").click()
    assert "My Account" in browser.find_element_by_tag_name("h1").text

    browser.find_element_by_id("edit-user-btn").click()

    browser.find_element_by_id("id_old_password").send_keys("test")
    browser.find_element_by_id("id_new_password1").send_keys("retest&987")
    browser.find_element_by_id("id_new_password2").send_keys("retest&987")

    browser.find_element_by_css_selector("input[type='submit']").click()

    assert (
        "Password successfully changed"
        in browser.find_element_by_tag_name("body").text
    )

    browser.find_element_by_link_text("Back to My Account").click()
    assert "My Account" in browser.find_element_by_tag_name("h1").text

    logout(browser)

    browser.get(f'{browser.server_url}{reverse("login")}')

    browser.find_element_by_id("login-teachers").click()

    username_input = browser.find_element_by_xpath(
        "//input[@id='id_username']"
    )
    username_input.clear()
    username_input.send_keys(teacher.user.username)

    password_input = browser.find_element_by_xpath(
        "//input[@id='id_password']"
    )
    password_input.clear()
    password_input.send_keys("retest&987")

    submit_button = browser.find_element_by_xpath(
        "//button[@id='submit-btn']"
    ).click()

    assert browser.current_url.endswith("saltise/lobby/")


def test_email_address_change(browser, assert_, teacher):
    new_email_address = "new_email_address@test.com"

    start(browser, teacher)
    browser.find_element_by_id("email-modify-btn").click()
    assert "Email Settings" in browser.find_element_by_tag_name("h1").text

    browser.find_element_by_id("id_email").send_keys(new_email_address)
    browser.find_element_by_id("submit-email-change-btn").click()
    assert "My Account" in browser.find_element_by_tag_name("h1").text

    browser.find_element_by_id("identity-section").click()
    browser.wait_for(
        lambda: assert_(
            new_email_address
            in browser.find_element_by_id("edit-user-btn").text
        )
    )


def test_email_notification_change(browser, teacher):
    start(browser, teacher)
    browser.find_element_by_id("email-modify-btn").click()
    assert "Email Settings" in browser.find_element_by_tag_name("h1").text

    assert not browser.find_element_by_id(
        "submit-notification-change-btn"
    ).is_enabled()

    browser.find_element_by_id("btn-toggle-all").click()
    browser.find_element_by_id("submit-notification-change-btn").click()
    assert "My Account" in browser.find_element_by_tag_name("h1").text

    # TODO: Send an email... outbox should be empty


def test_reset_password(browser, mail_outbox, teacher):
    browser.get(f'{browser.server_url}{reverse("password_reset")}')

    browser.find_element(By.ID, "id_email").send_keys(teacher.user.email)
    browser.find_element(By.ID, "submit-btn").click()

    WebDriverWait(browser, timeout=5).until(lambda d: len(mail_outbox) == 1)

    m = re.search(
        r"http[s]*://.*/reset/.*/.*/", mail_outbox[0].body
    )  # noqa W605
    signin_link = m[0]

    browser.get(signin_link)

    assert "Create a password" in browser.find_element_by_tag_name("h2").text

    browser.find_element_by_id("id_new_password1").send_keys("retest&987")
    browser.find_element_by_id("id_new_password2").send_keys("retest&987")

    browser.find_element_by_css_selector("input[type='submit']").click()

    assert "Success" in browser.page_source


def test_change_discipline_and_institution(
    browser, assert_, teacher, institution, discipline
):
    start(browser, teacher)
    browser.find_element_by_class_name("edit-identity-btn").click()
    assert (
        "Discipline and institution"
        in browser.find_element_by_tag_name("h2").text
    )

    Select(browser.find_element_by_id("id_institutions")).select_by_index(0)

    Select(browser.find_element_by_id("id_disciplines")).select_by_index(0)

    browser.find_element_by_id("update-identity").click()

    browser.find_element_by_id("identity-section").click()
    browser.wait_for(
        lambda: assert_(
            discipline.name
            in browser.find_element_by_class_name("edit-identity-btn").text
        )
    )
    browser.wait_for(
        lambda: assert_(
            institution.name
            in browser.find_elements_by_class_name("edit-identity-btn")[1].text
        )
    )
