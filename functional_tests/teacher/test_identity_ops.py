import time

from django.core.urlresolvers import reverse

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

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

    logout(browser, assert_)

    browser.get("{}{}".format(browser.server_url, reverse("login")))
    username_input = browser.find_element_by_xpath(
        "//input[@id=(//label[text()='Username']/@for)]"
    )
    username_input.clear()
    username_input.send_keys(teacher.user.username)

    password_input = browser.find_element_by_xpath(
        "//input[@id=(//label[text()='Password']/@for)]"
    )
    password_input.clear()
    password_input.send_keys("retest&987")

    submit_button = browser.find_element_by_xpath("//input[@value='Submit']")
    submit_button.click()

    assert browser.current_url.endswith("dashboard/")


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

    # TODO: Reset password... outbox should have 1 message


def test_change_discipline_and_institution(
    browser, assert_, teacher, institution
):
    start(browser, teacher)
    browser.find_element_by_class_name("edit-identity-btn").click()
    assert (
        "Discipline and institution"
        in browser.find_element_by_tag_name("h2").text
    )

    Select(browser.find_element_by_id("id_institutions")).select_by_value("1")

    browser.find_element_by_id("show_discipline_form").click()

    browser.wait_for(
        lambda: assert_(
            "Enter the name of a new discipline." in browser.page_source
        )
    )

    assert not browser.find_element_by_id("update-identity").is_enabled()

    input = browser.find_element_by_xpath(
        "//div[@id='discipline_create_form']/input[@id='id_title']"
    )
    # ENTER on a blank field throws form error
    input.send_keys(Keys.ENTER)
    browser.wait_for(
        lambda: assert_("This field is required" in browser.page_source)
    )

    # New discipline is accepted and switches to select form
    time.sleep(1)
    input = browser.find_element_by_xpath(
        "//div[@id='discipline_create_form']/input[@id='id_title']"
    )
    input.send_keys("My discipline")
    browser.find_element_by_id("submit_discipline_form").click()

    browser.wait_for(
        lambda: assert_(
            browser.find_element_by_id("update-identity").is_enabled()
        )
    )
    browser.find_element_by_id("update-identity").click()

    browser.find_element_by_id("identity-section").click()
    browser.wait_for(
        lambda: assert_(
            "My discipline"
            in browser.find_element_by_class_name("edit-identity-btn").text
        )
    )
    browser.wait_for(
        lambda: assert_(
            institution.name
            in browser.find_elements_by_class_name("edit-identity-btn")[1].text
        )
    )
