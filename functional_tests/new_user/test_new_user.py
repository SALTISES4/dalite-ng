import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
)
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa
from functional_tests.teacher.utils import go_to_account
from tos.models import Role, Tos

MAX_TIMEOUT = 10


def test_new_user_signup_workflow(
    browser, assert_, admin, mail_outbox, settings
):
    admin.username = settings.MANAGERS[0][0]
    admin.email = settings.MANAGERS[0][1]
    admin.save()

    # Hit landing page
    browser.get(f"{browser.server_url}/#Features")

    browser.wait_for(
        lambda: assert_(
            "Features" in browser.find_element_by_tag_name("h1").text
        )
    )
    browser.wait_for(
        lambda: assert_(
            "Login"
            in browser.find_element_by_id("link-to-login-or-welcome").text
        )
    )

    browser.find_element_by_id("accept-cookies").click()
    browser.find_element_by_id("link-to-signup").click()

    # Sign up page rendered
    browser.wait_for(
        lambda: assert_(
            "Sign Up" in browser.find_element_by_tag_name("h1").text
        )
    )

    # New user can sign up
    browser.wait_for(lambda: assert_(browser.find_element_by_tag_name("form")))
    form = browser.find_element_by_tag_name("form")
    assert form.get_attribute("method").lower() == "post"

    inputbox = browser.find_element_by_id("id_email")
    inputbox.send_keys("test@mydalite.org")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys("test")

    inputbox = browser.find_element_by_id("id_url")
    inputbox.clear()
    inputbox.send_keys("http://www.mydalite.org")

    browser.find_element_by_id("submit-btn").click()

    # New user redirected post sign up
    browser.wait_for(
        lambda: assert_(
            "Processing Request" in browser.find_element_by_tag_name("h1").text
        )
    )

    # New user cannot sign in
    browser.get(f"{browser.server_url}/saltise/login/")
    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys("test")

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("jka+sldfa+soih")

    browser.find_element_by_id("submit-btn").click()

    browser.wait_for(
        lambda: assert_(
            "your account has not yet been activated" in browser.page_source
        )
    )

    # Managers receive a notification
    assert len(mail_outbox) == 1
    for manager in settings.MANAGERS:
        assert manager[1] in mail_outbox[0].to

    # Manager approves on their dashboard
    m = re.search(
        "http[s]*://.*/.*/admin/saltise/new-user-approval", mail_outbox[0].body
    )
    dashboard_link = m[0]
    browser.get(dashboard_link)

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(admin.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys(settings.DEFAULT_PASSWORD)

    browser.find_element_by_xpath("//input[@type='submit']").click()

    browser.wait_for(
        lambda: assert_("New user approval" in browser.page_source)
    )

    browser.find_element_by_class_name("user__approve").click()

    browser.wait_for(lambda: assert_("No users to add" in browser.page_source))

    browser.get(f"{browser.server_url}/en/logout/")

    assert "login" in browser.current_url

    # Account verification email is sent to new user
    assert len(mail_outbox) == 2
    assert list(mail_outbox[0].to) == ["test@mydalite.org"]

    # Password reset email is sent to teacher
    m = re.search("http[s]*://.*/reset/.*", mail_outbox[0].body)
    verification_link = m[0]
    browser.get(verification_link)

    # Enter new password
    inputbox = browser.find_element_by_id("id_new_password1")
    inputbox.send_keys("jklasdf987")

    inputbox = browser.find_element_by_id("id_new_password2")
    inputbox.send_keys("jklasdf987")

    inputbox.submit()

    # Succesful save
    browser.wait_for(lambda: assert_("Success!" in browser.page_source))

    # Sign in
    browser.get(f"{browser.server_url}/saltise/login/")
    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys("test")

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("jklasdf987")

    browser.find_element_by_id("submit-btn").click()

    # Redirected to lobby
    assert browser.current_url.endswith("lobby/")


def test_inactive_user_login(browser, assert_, inactive_user):

    # Any inactive user cannot login
    browser.get(f"{browser.server_url}/saltise/login/")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(inactive_user.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("default_password")

    browser.find_element_by_id("submit-btn").click()

    browser.wait_for(
        lambda: assert_(
            "your account has not yet been activated" in browser.page_source
        )
    )


def test_new_teacher(browser, assert_, new_teacher, tos_teacher):

    # Teacher can login and access account
    browser.get(f"{browser.server_url}/saltise/login/")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(new_teacher.user.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("default_password")

    browser.find_element_by_id("submit-btn").click()

    assert browser.current_url.endswith("saltise/lobby/")

    dashboard = browser.find_element_by_xpath(
        "//a[contains(.,'My dashboard')]"
    ).click()

    # Redirected to dashboard
    assert browser.current_url.endswith("dashboard/")

    browser.find_element_by_id("accept-cookies").click()

    go_to_account(browser)

    # Access to account redirected to TOS if no TOS registered
    browser.wait_for(
        lambda: assert_(
            "Terms of Service"
            in browser.find_elements_by_tag_name("h1")[0].text
        )
    )

    browser.find_element_by_id("tos-accept").click()

    # Redirected to My Account and show TOS status
    browser.wait_for(
        lambda: assert_(
            "My Account" in browser.find_elements_by_tag_name("h1")[0].text
        )
    )
    assert "Terms of service: Sharing" in browser.page_source

    # Welcome authenticated user on landing page
    browser.get(browser.server_url)
    welcome = browser.find_element_by_id("link-to-login-or-welcome")
    browser.wait_for(
        lambda: assert_(
            f"Welcome back {new_teacher.user.username}" in welcome.text
        )
    )

    # Logout and log back in -> skip tos step
    browser.get(f"{browser.server_url}/logout")
    browser.get(f"{browser.server_url}/saltise/login/")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(new_teacher.user.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("default_password")

    browser.find_element_by_id("submit-btn").click()

    browser.find_element_by_xpath("//a[contains(.,'My dashboard')]").click()

    go_to_account(browser)

    browser.wait_for(
        lambda: assert_(
            "My Account" in browser.find_elements_by_tag_name("h1")[0].text
        )
    )

    # Add a new current TOS for teachers and refresh account -> back to tos
    role = Role.objects.get(role="teacher")
    new_TOS = Tos(version=2, text="Test 2", current=True, role=role)
    new_TOS.save()

    browser.get(f"{browser.server_url}/login")

    browser.find_element_by_xpath("//a[contains(.,'My dashboard')]").click()

    go_to_account(browser)

    browser.wait_for(
        lambda: assert_(
            "Terms of Service"
            in browser.find_elements_by_tag_name("h1")[0].text
        )
    )
    browser.find_element_by_id("tos-accept").click()

    # Teacher generally redirected to welcome page if logged in
    browser.get(f"{browser.server_url}/login")

    # Redirected to dashboard
    assert browser.current_url.endswith("lobby/")
