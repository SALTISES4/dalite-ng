import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa
from .utils import accept_cookies, go_to_account, login


def search(browser, assert_, realistic_questions):
    icon = browser.find_element_by_xpath("//i[contains(text(), 'menu')]")
    icon.click()

    try:
        forum_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Search database"))
        )
        time.sleep(1)
        forum_button.click()
    except NoSuchElementException:
        pass
    assert "Browse Database" in browser.find_element_by_tag_name("h1").text

    # Search
    inputbox = browser.find_element_by_id("search-bar")
    inputbox.send_keys(realistic_questions[0].title)
    inputbox.send_keys(Keys.ENTER)

    # Assert question in results
    try:
        element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.ID, "1"))
        )
    except NoSuchElementException:
        pass

    # Assert answer choices in response
    for ac in realistic_questions[0].answerchoice_set.all():
        assert ac.text in browser.page_source

    # Favourite a question
    fav_btn = browser.find_element_by_id(
        "favourite-btn-{}".format(realistic_questions[0].id)
    )
    ActionChains(browser).move_to_element(fav_btn).click(fav_btn).perform()

    time.sleep(1)

    # Check answer toggle
    top = browser.find_element_by_tag_name("h1")
    toggle = browser.find_element_by_id("toggle-answers")
    ActionChains(browser).move_to_element(top).click(toggle).perform()

    # Assert visible
    assert browser.find_elements_by_class_name("question-answers")[
        0
    ].is_displayed()

    # Assert filters rendered
    assert browser.find_element_by_id("filters").is_displayed()

    count = len(browser.find_elements_by_class_name("mdc-card"))

    # Check category filter
    category = realistic_questions[0].category.first()
    filter = browser.find_element_by_css_selector(
        ".mdc-chip[c*='{}']".format(category)
    ).click()
    recount = 0
    for card in browser.find_elements_by_class_name("mdc-card"):
        if card.is_displayed():
            recount += 1
            assert category.title in card.text

    assert recount <= count

    # Check clear
    browser.find_element_by_id("reset-filters").click()
    recount = 0
    for card in browser.find_elements_by_class_name("mdc-card"):
        if card.is_displayed():
            recount += 1
    assert recount == count

    # Check re-search
    inputbox.clear()
    inputbox.send_keys(realistic_questions[1].title)
    inputbox.send_keys(Keys.ENTER)

    # Assert question in results
    try:
        element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.ID, "2"))
        )
    except NoSuchElementException:
        pass

    # Check only valid questions are searchable?
    inputbox.clear()
    inputbox.send_keys(realistic_questions[-1].title)
    inputbox.send_keys(Keys.ENTER)

    # Assert question not in results
    browser.wait_for(
        lambda: assert_(
            realistic_questions[-1].title
            not in browser.find_elements_by_class_name("search-set")[0].text
        )
    )


def check_favourites(browser, teacher, question, assignment):
    go_to_account(browser)
    browser.find_element_by_id("assignment-section").click()
    browser.find_element_by_id(
        "edit-assignment-{}".format(assignment.identifier)
    ).click()

    assert (
        "Update Assignment" in browser.find_elements_by_tag_name("h1")[0].text
    )

    fav_questions = browser.find_element_by_id("favourite-questions")
    fav_questions.click()

    time.sleep(1)
    assert question.text in fav_questions.text


def test_search_function(
    browser, assert_, teacher, realistic_questions, assignment
):
    login(browser, teacher)
    accept_cookies(browser)
    search(browser, assert_, realistic_questions)
    teacher.assignments.add(assignment)
    assignment.owner.add(teacher.user)
    check_favourites(browser, teacher, realistic_questions[0], assignment)
