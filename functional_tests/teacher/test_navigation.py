from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa

from .utils import accept_cookies, login, logout

MAX_WAIT = 10


def start(browser, teacher):
    login(browser, teacher)
    accept_cookies(browser)


def test_change_language(browser, teacher):
    start(browser, teacher)
    browser.find_element_by_xpath("//i[contains(text(), 'menu')]").click()

    assert "en/teacher/dashboard/" in browser.current_url

    WebDriverWait(browser, MAX_WAIT).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//i[contains(text(), 'language')]")
        )
    ).click()

    assert "fr/teacher/dashboard/" in browser.current_url
