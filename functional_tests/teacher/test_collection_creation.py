from faker import Faker
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
)
from selenium.webdriver.support.ui import WebDriverWait, Select

from functional_tests.fixtures import *  # noqa
from .utils import login
from django.urls import reverse
import time


fake = Faker()
timeout = 3


def create_collection(browser, assert_, teacher):
    # go to collection list view and click on create admin link
    browser.get("{}{}".format(browser.server_url, reverse("collection-list")))

    browser.find_element_by_link_text("Create").click()
    # make sure that the user is on create view and has all its components
    try:
        create = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "collection-create-form"))
        )
    except TimeoutException:
        assert False

    assert browser.current_url.endswith("create/")

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert "Create a Collection" in browser.find_element_by_tag_name("h2").text

    assert (
        "Please use this page to create your collection of assignments."
        in browser.find_element_by_tag_name("p").text
    )

    assert "Title" in browser.page_source
    assert "Description" in browser.page_source
    assert "Discipline" in browser.page_source
    assert "Thumbnail image" in browser.page_source
    assert "Private" in browser.page_source

    # provide collection info
    title = fake.sentence(nb_words=4)
    description = fake.sentence(nb_words=6)

    browser.find_element_by_id("id_title").send_keys(title)
    browser.find_element_by_id("id_description").send_keys(description)
    Select(browser.find_element_by_id("id_discipline")).select_by_value("1")
    browser.find_element_by_id("id_private").click()
    # go to update view
    browser.find_element_by_id("id_create").click()

    # assure user has reached update view
    try:
        page_id = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "collection-update-form"))
        )
    except TimeoutException:
        assert False

    # add an assignment to the collection
    browser.find_element_by_class_name("foldable--title").click()

    browser.find_element_by_class_name("follower-btn").click()
    # leave page
    browser.find_element_by_id("id_update").click()

    # assure user has reached detail page
    try:
        detail = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "obj.desc"))
        )
    except TimeoutException:
        assert False

    assert "Collection Statistics" in browser.page_source
    assert title in browser.find_element_by_tag_name("h2").text
    assert description in browser.find_element_by_id("obj.desc").text
    assert ("Created by") in browser.find_element_by_class_name(
        "mdc-typography--caption"
    ).text

    # edit the collection
    browser.find_element_by_link_text("Edit").click()
    # assure user is on update view
    try:
        update = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "collection-update-form"))
        )
    except TimeoutException:
        assert False

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert (
        "Edit Your Collection" in browser.find_element_by_tag_name("h2").text
    )

    assert (
        "Please use this page to edit your collection of assignments."
        in browser.find_element_by_tag_name("p").text
    )

    assert "Title" in browser.page_source
    assert "Description" in browser.page_source
    assert "Discipline" in browser.page_source
    assert "Thumbnail image" in browser.page_source
    assert "Private" in browser.page_source
    # update the collection
    title_update = fake.sentence(nb_words=4)
    description_update = fake.sentence(nb_words=6)

    browser.find_element_by_id("id_title").clear()
    browser.find_element_by_id("id_description").clear()

    browser.find_element_by_id("id_title").send_keys(title_update)
    browser.find_element_by_id("id_description").send_keys(description_update)
    Select(browser.find_element_by_id("id_discipline")).select_by_value("1")
    browser.find_element_by_id("id_private").click()
    # update info, leave update view
    browser.find_element_by_id("id_update").click()
    # assure user is on detail view
    try:
        detail = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "obj.desc"))
        )
    except TimeoutException:
        assert False

    assert "Collection Statistics" in browser.page_source
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert title_update in browser.find_element_by_tag_name("h2").text
    assert description_update in browser.find_element_by_id("obj.desc").text
    assert ("Created by") in browser.find_element_by_class_name(
        "mdc-typography--caption"
    ).text
    # delete collection
    browser.find_element_by_link_text("Delete").click()
    # assure user is on delete view
    try:
        delete_form = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "collection-delete-form"))
        )
    except TimeoutException:
        assert False

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert "Delete Collection" in browser.find_element_by_tag_name("h2").text
    assert (
        "Are you sure you would like to delete your collection of assignments?"
        in browser.find_element_by_tag_name("p").text
    )
    assert (
        "You will be unable to retrieve any information regarding this collect"
        in browser.page_source
    )
    assert "Confirm" in browser.page_source
    # confirm deletion
    browser.find_element_by_id("id_delete").click()
    # assure user is on correct list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert "Browse Collections" in browser.find_element_by_tag_name("h2").text
    # assure collection has been deleted
    assert browser.current_url.endswith("collection/list/")
    assert description not in browser.page_source
    # go to featured list view
    browser.find_element_by_link_text("Featured").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert (
        "Featured Collections" in browser.find_element_by_tag_name("h2").text
    )
    # go to personal list view
    browser.find_element_by_link_text("Owned").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert "Your Collections" in browser.find_element_by_tag_name("h2").text
    # go to followed list view
    browser.find_element_by_link_text("Followed").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert (
        "Followed Collections" in browser.find_element_by_tag_name("h2").text
    )
    # go to general list view
    browser.find_element_by_link_text("All").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert "Browse Collections" in browser.find_element_by_tag_name("h2").text


def collection_buttons(
    browser, assert_, teacher, group, student_group_assignment
):
    # access group from teacher detail page
    browser.find_element_by_link_text("Back to My Account").click()
    browser.find_element_by_id("groups-section").click()
    browser.find_element_by_class_name("md-48").click()
    # open assignment foldable and add assignments to collection
    browser.find_element_by_xpath("//h2[@id='assignments-title']").click()
    browser.find_element_by_id("collection-select").click()
    # assure user is on update view
    try:
        create = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "collection-update-form"))
        )
    except TimeoutException:
        assert False

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert (
        "Edit Your Collection" in browser.find_element_by_tag_name("h2").text
    )

    assert (
        "Please use this page to edit your collection of assignments."
        in browser.find_element_by_tag_name("p").text
    )

    assert "Title" in browser.page_source
    assert "Description" in browser.page_source
    assert "Discipline" in browser.page_source
    assert "Thumbnail image" in browser.page_source
    assert "Private" in browser.page_source
    # provide update info
    title = fake.sentence(nb_words=4)
    description = fake.paragraph(nb_sentences=1, variable_nb_sentences=False)

    browser.find_element_by_id("id_title").send_keys(title)
    browser.find_element_by_id("id_description").send_keys(description)
    # confirm update
    browser.find_element_by_id("id_update").click()
    # assure user is on detail view
    try:
        detail = WebDriverWait(browser, timeout).until(
            presence_of_element_located((By.ID, "obj.desc"))
        )
    except TimeoutException:
        assert False

    assert "Collection Statistics" in browser.page_source
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    # click on assign button
    browser.find_element_by_class_name("mdc-button").click()
    # assure user is on distribute detail view
    assert (
        "Your may assign the this collection to one of your student groups by"
        in browser.find_element_by_tag_name("small").text
    )
    # assure unassign is preselected
    assert "UNASSIGN" in browser.find_element_by_tag_name("button").text
    # click on unassign button
    browser.find_element_by_class_name("collection-toggle-assign").click()
    # assure button changes to assign
    assert "ASSIGN" in browser.find_element_by_tag_name("button").text
    # go to group
    browser.find_element_by_id("group-title").click()
    # assure on group detail view
    assert (
        group.title
        in browser.find_element_by_class_name(
            "mdc-list-item__secondary-text"
        ).text
    )
    # open assignments foldable
    browser.find_element_by_xpath("//h2[@id='assignments-title']").click()
    # assure assignment has been removed
    assert student_group_assignment.assignment.title not in browser.page_source
    # go back to distribute detail view
    browser.execute_script("window.history.go(-1)")
    # assure button shows "assign "
    assert "ASSIGN" in browser.find_element_by_class_name("mdc-button").text
    # click on assign
    browser.find_element_by_class_name("collection-toggle-assign").click()
    time.sleep(5)
    # assure button changes to unassign
    assert "UNASSIGN" in browser.find_element_by_class_name("mdc-button").text
    # go to group page
    browser.find_element_by_id(group.hash).click()
    # assure on group detail view
    assert (
        group.title
        in browser.find_element_by_class_name(
            "mdc-list-item__secondary-text"
        ).text
    )
    # open assignments foldable
    browser.find_element_by_xpath("//h2[@id='assignments-title']").click()
    # assure assignments have been added to group
    assert student_group_assignment.assignment.title in browser.page_source


def test_create_collection(
    browser,
    assert_,
    teacher,
    discipline,
    assignment,
    group,
    undistributed_assignment,
):
    teacher.disciplines.add(discipline)
    teacher.assignments.add(assignment)
    assignment.owner.add(teacher.user)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    login(browser, teacher)
    create_collection(browser, assert_, teacher)
    collection_buttons(
        browser, assert_, teacher, group, undistributed_assignment
    )
