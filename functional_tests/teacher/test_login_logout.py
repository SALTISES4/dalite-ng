from functional_tests.fixtures import *  # noqa

from .utils import accept_cookies, login, logout


def access_logged_in_account_from_landing_page(browser, teacher):
    browser.get(browser.server_url)
    browser.find_element_by_link_text(
        f"Welcome back, {teacher.user.username}"
    ).click()

    assert browser.current_url.endswith("saltise/lobby/")

    browser.find_element_by_xpath("//a[contains(.,'My dashboard')]").click()

    assert browser.current_url.endswith("teacher/dashboard/")


def test_teacher_login_logout(browser, teacher):
    login(browser, teacher)
    accept_cookies(browser)
    access_logged_in_account_from_landing_page(browser, teacher)
    logout(browser)
