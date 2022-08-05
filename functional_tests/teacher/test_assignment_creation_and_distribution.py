from faker import Faker
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
)
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.fixtures import *  # noqa

from .utils import go_to_account, login

fake = Faker()
timeout = 3


def create_assignment(browser, teacher, complete_questions):
    WebDriverWait(browser, timeout).until(
        presence_of_element_located(
            (By.XPATH, "//h2[contains(.,'Assignments')]")
        )
    ).click()

    WebDriverWait(browser, timeout).until(
        presence_of_element_located(
            (By.XPATH, "//span[contains(.,'Create new')]")
        )
    ).click()

    try:
        identifier = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "id_identifier"))
        )
    except TimeoutException:
        assert False

    identifier.send_keys("test")

    title = browser.find_element_by_id("id_title")
    title.send_keys(fake.sentence(nb_words=5))

    tinymce_embed = browser.find_element_by_id("id_description_ifr")
    browser.switch_to.frame(tinymce_embed)
    browser.find_element_by_id("tinymce").send_keys(fake.paragraph())
    browser.switch_to.default_content()

    tinymce_embed = browser.find_element_by_id("id_intro_page_ifr")
    browser.switch_to.frame(tinymce_embed)
    browser.find_element_by_id("tinymce").send_keys(fake.paragraph())
    browser.switch_to.default_content()

    tinymce_embed = browser.find_element_by_id("id_conclusion_page_ifr")
    browser.switch_to.frame(tinymce_embed)
    browser.find_element_by_id("tinymce").send_keys(fake.paragraph())
    browser.switch_to.default_content()

    create = browser.find_element_by_xpath("//input[@value='Create']")
    create.click()

    search = browser.find_element_by_id("search-db-app").find_element_by_xpath(
        "//input[@type='text']"
    )
    search.send_keys(teacher.user.username)

    """
    # rmwc throws console error

    search.send_keys(Keys.ENTER)
    try:
        question = WebDriverWait(browser, timeout).until(
            presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@class='mdc-card']//button[@title='Add this question to this assignment']",  # noqa E501
                )
            )
        )
    except TimeoutException:
        assert False

    question.click()
    """

    link = browser.find_element_by_link_text("Back to My Account").click()


def create_group(browser):
    try:
        WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.XPATH, "//h2[text()='Groups']"))
        ).click()
    except TimeoutException:
        assert False
    browser.find_element_by_link_text("Manage groups").click()

    try:
        title = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "id_title"))
        )
    except TimeoutException:
        assert False

    title.send_keys("test")

    name = browser.find_element_by_id("id_name")
    name.send_keys("test")

    create = browser.find_element_by_xpath("//input[@value='Create']")
    create.click()

    link = browser.find_element_by_link_text(
        "Back to My Account"
    ).get_attribute("href")
    browser.get(link)


def distribute_assignment(browser):
    try:
        WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "assignment-section"))
        ).click()
    except TimeoutException:
        assert False

    browser.find_element_by_xpath(
        "//h2[@id='assignment-section']/..//i[text()='share']"
    ).click()

    try:
        WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.XPATH, "//input[@value='Assign']"))
        ).click()
    except TimeoutException:
        assert False

    try:
        WebDriverWait(browser, timeout).until(
            presence_of_element_located(
                (By.XPATH, "//span[@id='assignment-distribution']/button")
            )
        ).click()
    except TimeoutException:
        assert False

    try:
        WebDriverWait(browser, timeout).until(
            presence_of_element_located(
                (
                    By.XPATH,
                    "//span[@id='assignment-distribution' "
                    "and contains(text(),'Distributed')]",
                )
            )
        )
    except TimeoutException:
        assert False


def test_assignment_creation_and_distribution(
    browser, discipline, questions, teacher
):
    for q in questions:
        q.user = teacher.user
        q.discipline = discipline
        q.save()
    login(browser, teacher)
    go_to_account(browser)
    create_assignment(browser, teacher, questions)
    # create_group(browser)
    # distribute_assignment(browser)
