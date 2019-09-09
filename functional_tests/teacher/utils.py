import time

from django.core.urlresolvers import reverse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa


def accept_cookies(browser):
    browser.find_element_by_id("accept-cookies").click()


def go_to_account(browser):
    icon = browser.find_element_by_xpath("//i[contains(text(), 'menu')]")
    icon.click()

    try:
        account_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "My account"))
        )
        time.sleep(1)
        account_button.click()
    except NoSuchElementException:
        pass


def login(browser, teacher):
    username = teacher.user.username
    password = "test"

    browser.get("{}{}".format(browser.server_url, reverse("login")))

    username_input = browser.find_element_by_xpath(
        "//input[@id=(//label[text()='Username']/@for)]"
    )
    username_input.clear()
    username_input.send_keys(username)

    password_input = browser.find_element_by_xpath(
        "//input[@id=(//label[text()='Password']/@for)]"
    )
    password_input.clear()
    password_input.send_keys(password)

    submit_button = browser.find_element_by_xpath("//input[@value='Submit']")
    submit_button.click()

    assert browser.current_url.endswith("teacher/dashboard/")


def logout(browser, assert_):
    icon = browser.find_element_by_xpath("//i[contains(text(), 'menu')]")
    icon.click()

    logout_button = browser.find_element_by_link_text("Logout")
    browser.wait_for(assert_(logout_button.is_enabled()))
    # FIXME:
    # Assertion shoud include logout_button.is_displayed() but throws w3c error
    time.sleep(1)
    logout_button.click()

    assert browser.current_url == browser.server_url + "/en/"

    browser.find_element_by_link_text("Login")
    browser.find_element_by_link_text("Signup")
