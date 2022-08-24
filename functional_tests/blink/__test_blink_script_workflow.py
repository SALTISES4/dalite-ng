import time

from django.urls import reverse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa
from functional_tests.teacher.utils import accept_cookies, go_to_account, login

TIME = 15


def make_blink_script(browser, q):
    browser.find_element_by_id("blink-section").click()
    browser.find_element_by_link_text("Add script").click()

    script_name = "New blink script"

    title_field = browser.find_element_by_id("id_title")
    title_field.send_keys(script_name)
    title_field.send_keys(Keys.ENTER)

    assert "Update Script" in browser.find_element_by_tag_name("h1").text
    assert script_name in browser.find_element_by_id("assignment").text

    checkbox = browser.find_element_by_id("limit-search")
    checkbox.click()

    search = browser.find_element_by_id("search-bar")
    search.send_keys(q[0].title)
    search.send_keys(Keys.ENTER)

    time.sleep(1)
    assert q[0].title in browser.find_element_by_id("search_results").text

    card = browser.find_element_by_id(f"add-{q[0].pk}").click()

    search = browser.find_element_by_id("search-bar")
    search.send_keys(q[1].title)
    search.send_keys(Keys.ENTER)

    time.sleep(1)
    assert q[1].title in browser.find_element_by_id("search_results").text

    card = browser.find_element_by_id(f"add-{q[1].pk}").click()

    go_to_account(browser)


def start_blink_script(browser):
    link = browser.find_element_by_class_name("blink")
    link.click()

    time_field = browser.find_element_by_id("id_time_limit")
    time_field.clear()
    time_field.send_keys(TIME)

    start_btn = browser.find_element_by_xpath("//input[@value='Start']")
    start_btn.click()


def validate_teacher_page(browser, q):
    assert "Blink Question" in browser.find_element_by_tag_name("h1").text
    assert q.title in browser.find_element_by_id("question-title").text


def validate_student_page(second_browser, q):
    try:
        WebDriverWait(second_browser, timeout=10).until(
            EC.element_to_be_clickable((By.ID, "submit-answer"))
        )
    except TimeoutException:
        pass

    print(second_browser.page_source)

    assert (
        "Blink Question" in second_browser.find_element_by_tag_name("h1").text
    )
    assert q.title in second_browser.find_element_by_id("question-title").text
    assert len(second_browser.find_elements_by_class_name("mdc-radio")) > 0


def answer_blink(second_browser, q, choice):
    second_browser.find_elements_by_class_name("mdc-radio")[choice].click()
    second_browser.find_element_by_id("submit-answer").click()

    assert (
        "Blink Question" in second_browser.find_element_by_tag_name("h1").text
    )
    assert q.title in second_browser.find_element_by_id("question-title").text
    assert len(second_browser.find_elements_by_class_name("mdc-radio")) == 0


def test_blink_script(
    browser, second_browser, assert_, realistic_questions, teacher
):
    print("Start")
    browser.set_window_rect(0, 0, 1000, 1200)
    second_browser.set_window_rect(1000, 0, 1000, 1200)

    blink_url = "{}{}".format(
        browser.server_url,
        reverse("blink:blink-waiting", args=(teacher.user.username,)),
    )
    second_browser.get(blink_url)
    accept_cookies(second_browser)
    assert (
        "Waiting for teacher"
        in second_browser.find_element_by_tag_name("h2").text
    )

    login(browser, teacher)
    accept_cookies(browser)
    go_to_account(browser)
    make_blink_script(browser, realistic_questions[:2])
    start_blink_script(browser)

    validate_teacher_page(browser, realistic_questions[0])
    validate_student_page(second_browser, realistic_questions[0])

    answer_blink(second_browser, realistic_questions[0], 0)

    reset_button = WebDriverWait(browser, timeout=2 * TIME).until(
        EC.element_to_be_clickable((By.ID, "reset_button"))
    )

    assert browser.find_element_by_id("round").text == "1"
    assert browser.find_element_by_id("counter").text == "1"

    reset_button.click()

    validate_teacher_page(browser, realistic_questions[0])
    validate_student_page(second_browser, realistic_questions[0])

    answer_blink(second_browser, realistic_questions[0], 1)

    assert browser.find_element_by_id("round").text == "2"
    assert browser.find_element_by_id("counter").text == "1"

    next_button = WebDriverWait(browser, timeout=2 * TIME).until(
        EC.element_to_be_clickable((By.ID, "next_button"))
    )
    next_button.click()

    validate_teacher_page(browser, realistic_questions[1])
    validate_student_page(second_browser, realistic_questions[1])

    answer_blink(second_browser, realistic_questions[1], 2)
    assert browser.find_element_by_id("round").text == "1"
    assert browser.find_element_by_id("counter").text == "1"

    browser.find_element_by_id("next_button").click()
    time.sleep(2)
    assert (
        "Waiting for teacher"
        in second_browser.find_element_by_tag_name("h2").text
    )
    assert "My Account" in browser.find_element_by_tag_name("h1").text
