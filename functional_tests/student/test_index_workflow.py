import re

from django.urls import reverse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import (
    invisibility_of_element_located,
    presence_of_element_located,
    text_to_be_present_in_element,
    visibility_of_element_located,
)
from selenium.webdriver.support.ui import Select, WebDriverWait

from functional_tests.fixtures import *  # noqa

timeout = 1


def signin(browser, student, mail_outbox):
    email = student.student.email

    browser.get(f'{browser.server_url}{reverse("login")}')

    browser.find_element_by_xpath(
        "//button[contains(.,'Login via email')]"
    ).click()

    input_ = browser.find_element_by_name("email")
    input_.clear()
    input_.send_keys(email)
    input_.send_keys(Keys.ENTER)

    assert len(mail_outbox) == 1
    assert list(mail_outbox[0].to) == [email]

    m = re.search(
        r"http[s]*://.*/student/\?token=.*", mail_outbox[0].body
    )  # noqa W605
    signin_link = m[0]

    browser.get(signin_link)

    assert re.search(r"student/", browser.current_url)


def join_group_with_link(browser, group):
    link = "{}{}".format(
        browser.server_url,
        reverse("signup-through-link", kwargs={"group_hash": group.hash}),
    )

    add_group = browser.find_element_by_xpath(
        "//span[contains(string(), 'Add group')]"
    )
    add_group.click()

    input_ = browser.find_element_by_name("new-group")
    input_.clear()
    input_.send_keys(link)
    input_.send_keys(Keys.ENTER)

    try:
        WebDriverWait(browser, timeout).until(
            presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@class='student-group--title']/"
                    "h3[text()='{}']".format(group.title),
                )
            )
        )
    except TimeoutException:
        assert False


def leave_group(browser, group):

    leaveBtn = browser.find_element_by_xpath(
        "//div[@class='student-group--remove']/i"
    )
    leaveBtn.click()

    leave = browser.find_element_by_xpath("//button[text()='Leave']")
    leave.click()

    # try:
    #     WebDriverWait(browser, timeout).until(
    #         invisibility_of_element_located(
    #             (
    #                 By.XPATH,
    #                 "//div[@class='student-group--title']/"
    #                 "h3[text()='{}']".format(group.title),
    #             )
    #         )
    #     )
    # except TimeoutException:
    #     assert False


def join_old_group(browser, group):
    add_group = browser.find_element_by_xpath(
        "//span[contains(string(), 'Add group')]"
    )
    add_group.click()

    select = Select(browser.find_element_by_id("student-old-groups"))
    select.select_by_visible_text(group.title)

    join = browser.find_element_by_id("join-group-btn")
    join.click()

    browser.find_element_by_xpath(
        "//div[@class='student-group--title']/"
        "h3[text()='{}']".format(group.title)
    )


def toggle_notification(browser):
    icon = browser.find_element_by_xpath(
        "//div[@class='student-group--title']//i[text()='notifications']"
    )
    icon.click()

    assert icon.text == "notifications_off"
    assert "student-group--notifications__disabled" in icon.get_attribute(
        "class"
    )

    icon.click()

    assert icon.text == "notifications"
    assert "student-group--notifications__disabled" not in icon.get_attribute(
        "class"
    )


def change_student_id(browser):
    #  copy_xpath = "//div[@class='student-group--title']//i[text()='file_copy']"  # noqa
    span_xpath = (
        "//div[@class='student-group--title']//"
        "span[@class='student-group--id__id']"
    )
    input_xpath = (
        "//div[@class='student-group--title']//"
        "input[@class='student-group--id__input']"
    )
    edit_xpath = "//div[@class='student-group--title']//i[text()='edit']"
    check_xpath = "//div[@class='student-group--title']//i[text()='check']"
    cancel_xpath = "//div[@class='student-group--title']//i[text()='close']"
    #  copy = browser.find_element_by_xpath(copy_xpath)
    span = browser.find_element_by_xpath(span_xpath)
    input_ = browser.find_element_by_xpath(input_xpath)
    edit = browser.find_element_by_xpath(edit_xpath)
    check = browser.find_element_by_xpath(check_xpath)
    cancel = browser.find_element_by_xpath(cancel_xpath)

    try:
        #  WebDriverWait(browser, timeout).until(
        #  visibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, cancel_xpath))
        )
    except TimeoutException:
        assert False

    edit.click()

    try:
        #  WebDriverWait(browser, timeout).until(
        #  invisibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, cancel_xpath))
        )
    except TimeoutException:
        assert False

    input_.clear()
    input_.send_keys("test1")
    input_.send_keys(Keys.ENTER)

    try:
        #  WebDriverWait(browser, timeout).until(
        #  visibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, cancel_xpath))
        )
        WebDriverWait(browser, timeout).until(
            text_to_be_present_in_element((By.XPATH, span_xpath), "test1")
        )
    except TimeoutException:
        assert False

    span.click()

    try:
        #  WebDriverWait(browser, timeout).until(
        #  invisibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, cancel_xpath))
        )
    except TimeoutException:
        assert False

    input_.clear()
    input_.send_keys("test2")

    check.click()

    try:
        #  WebDriverWait(browser, timeout).until(
        #  visibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, cancel_xpath))
        )
        WebDriverWait(browser, timeout).until(
            text_to_be_present_in_element((By.XPATH, span_xpath), "test2")
        )
    except TimeoutException:
        assert False

    edit.click()

    try:
        #  WebDriverWait(browser, timeout).until(
        #  invisibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, cancel_xpath))
        )
    except TimeoutException:
        assert False

    input_.clear()
    input_.send_keys("test3")

    cancel.click()

    try:
        #  WebDriverWait(browser, timeout).until(
        #  visibility_of_element_located((By.XPATH, copy_xpath))
        #  )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, span_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, input_xpath))
        )
        WebDriverWait(browser, timeout).until(
            visibility_of_element_located((By.XPATH, edit_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, check_xpath))
        )
        WebDriverWait(browser, timeout).until(
            invisibility_of_element_located((By.XPATH, cancel_xpath))
        )
        WebDriverWait(browser, timeout).until(
            text_to_be_present_in_element((By.XPATH, span_xpath), "test2")
        )
    except TimeoutException:
        assert False

    #  copy.click()


#
#  try:
#  bubble = WebDriverWait(browser, timeout).until(
#  visibility_of_element_located((By.CLASS_NAME, "bubble"))
#  )
#  except TimeoutException:
#  assert False
#
#  assert bubble.text == "Copied to clipboard!"


def test_index_workflow(browser, student, group, mail_outbox):
    group.student_id_needed = True
    group.save()
    signin(browser, student, mail_outbox)
    join_group_with_link(browser, group)
    leave_group(browser, group)
    join_old_group(browser, group)
    toggle_notification(browser)
    change_student_id(browser)
