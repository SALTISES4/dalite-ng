import re

from functional_tests.fixtures import *  # noqa
from functional_tests.teacher.utils import go_to_account
from tos.models import Role, Tos


def test_new_user_signup_workflow(
    browser, assert_, admin, mailoutbox, settings
):
    settings.ADMINS = (admin.username, admin.email)

    # Hit landing page
    browser.get(browser.server_url + "/#Features")

    browser.find_element_by_id("accept-cookies").click()

    browser.wait_for(
        lambda: assert_(
            "Features" in browser.find_element_by_tag_name("h1").text
        )
    )
    assert (
        "Login" in browser.find_element_by_id("link-to-login-or-welcome").text
    )
    browser.find_element_by_link_text("Signup").click()

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
    inputbox.send_keys("test@test.com")

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
    browser.get(browser.server_url + "/login")
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

    # Admins receive notification
    assert len(mailoutbox) == 1
    assert list(mailoutbox[0].to) == [a[1] for a in settings.ADMINS]

    # Admin approves on their dashboard
    m = re.search("http[s]*://.*/dashboard/", mailoutbox[0].body)
    dashboard_link = m.group(0)
    browser.get(dashboard_link)

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(admin.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("default_password")

    browser.find_element_by_id("submit-btn").click()

    browser.wait_for(lambda: assert_("Inactive users" in browser.page_source))

    form = browser.find_element_by_xpath("//form[contains(@id, 'activate')]")
    browser.find_element_by_xpath("//input[@type='checkbox']").click()
    form.submit()

    browser.wait_for(lambda: assert_("No users to add" in browser.page_source))

    browser.get(browser.server_url + "/logout")

    # Notification email is sent to teacher
    assert len(mailoutbox) == 2
    assert list(mailoutbox[1].to) == ["test@test.com"]

    m = re.search("http[s]*://.*/reset/.*", mailoutbox[1].body)
    verification_link = m.group(0)
    browser.get(verification_link)

    # Enter new password
    inputbox = browser.find_element_by_id("id_new_password1")
    inputbox.send_keys("jklasdf987")

    inputbox = browser.find_element_by_id("id_new_password2")
    inputbox.send_keys("jklasdf987")

    inputbox.submit()

    # Succesful save
    browser.wait_for(lambda: assert_("Success!" in browser.page_source))

    browser.find_element_by_link_text("Login").click()

    browser.wait_for(lambda: assert_("login" in browser.current_url))

    # Sign in
    browser.get(browser.server_url + "/login")
    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys("test")

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("jklasdf987")

    browser.find_element_by_id("submit-btn").click()

    # Redirected to dashboard
    assert browser.current_url.endswith("dashboard/")


def test_new_user_signup_with_email_server_error(browser, assert_, settings):
    settings.EMAIL_BACKEND = ""

    browser.get(browser.server_url + "/signup")

    browser.find_element_by_id("accept-cookies").click()

    form = browser.find_element_by_tag_name("form")
    assert form.get_attribute("method") == "post"

    inputbox = browser.find_element_by_id("id_email")
    inputbox.send_keys("test@test.com")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys("test")

    inputbox = browser.find_element_by_id("id_url")
    inputbox.clear()
    inputbox.send_keys("http://www.mydalite.org")

    browser.find_element_by_id("submit-btn").click()

    browser.wait_for(
        lambda: assert_(
            "An error occurred while processing your request"
            in browser.page_source
        )
    )


def test_inactive_user_login(browser, assert_, inactive_user):

    # Any inactive user cannot login
    browser.get(browser.server_url + "/login")

    browser.find_element_by_id("accept-cookies").click()

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
    browser.get(browser.server_url + "/login")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(new_teacher.user.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("default_password")

    browser.find_element_by_id("submit-btn").click()

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
            "Welcome back " + new_teacher.user.username in welcome.text
        )
    )

    # Logout and log back in -> skip tos step
    browser.get(browser.server_url + "/logout")
    browser.get(browser.server_url + "/login")

    inputbox = browser.find_element_by_id("id_username")
    inputbox.send_keys(new_teacher.user.username)

    inputbox = browser.find_element_by_id("id_password")
    inputbox.send_keys("default_password")

    browser.find_element_by_id("submit-btn").click()

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

    browser.get(browser.server_url + "/login")

    go_to_account(browser)

    browser.wait_for(
        lambda: assert_(
            "Terms of Service"
            in browser.find_elements_by_tag_name("h1")[0].text
        )
    )
    browser.find_element_by_id("tos-accept").click()

    # Teacher generally redirected to welcome page if logged in
    browser.get(browser.server_url + "/login")

    # Redirected to dashboard
    assert browser.current_url.endswith("dashboard/")
