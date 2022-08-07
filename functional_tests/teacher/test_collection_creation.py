import time

from django.urls import reverse
from faker import Faker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
)
from selenium.webdriver.support.ui import Select, WebDriverWait

from functional_tests.fixtures import *  # noqa

from .utils import accept_cookies, login

fake = Faker()
timeout = 10


def create_collection(browser, assert_, teacher):
    # go to collection list view and click on create admin link
    browser.get(f'{browser.server_url}{reverse("collection-list")}')

    browser.find_element_by_link_text("Create").click()
    # make sure that the user is on create view and has all its components
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "collection-create-form"))
    )

    assert browser.current_url.endswith("create/")

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Create a Collection"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    assert (
        "Please use this page to create your collection of assignments."
        in browser.page_source
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
    Select(browser.find_element_by_id("id_discipline")).select_by_index(1)
    browser.find_element_by_id("id_private").click()
    # go to update view
    browser.find_element_by_id("id_create").click()

    # assure user has reached update view
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "collection-update-form"))
    )

    # add an assignment to the collection
    browser.find_element_by_class_name("foldable--title").click()

    browser.find_element_by_class_name("follower-btn").click()
    # leave page
    browser.find_element_by_id("id_update").click()

    # assure user has reached detail page
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "obj.desc"))
    )

    assert "Collection Statistics" in browser.page_source
    assert any(
        title == h2.text for h2 in browser.find_elements_by_tag_name("h2")
    )
    assert description in browser.find_element_by_id("obj.desc").text
    assert ("Created by") in browser.find_element_by_class_name(
        "mdc-typography--caption"
    ).text

    # edit the collection
    browser.find_element_by_link_text("Edit").click()
    # assure user is on update view

    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "collection-update-form"))
    )

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Edit Your Collection"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    assert (
        "Please use this page to edit your collection of assignments."
        in browser.page_source
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
    Select(browser.find_element_by_id("id_discipline")).select_by_index(1)
    browser.find_element_by_id("id_private").click()
    # update info, leave update view
    browser.find_element_by_id("id_update").click()
    # assure user is on detail view
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "obj.desc"))
    )

    assert "Collection Statistics" in browser.page_source
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        title_update == h2.text
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    assert description_update in browser.find_element_by_id("obj.desc").text
    assert ("Created by") in browser.find_element_by_class_name(
        "mdc-typography--caption"
    ).text
    # delete collection
    browser.find_element_by_link_text("Delete").click()
    # assure user is on delete view
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "collection-delete-form"))
    )

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Delete Collection"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    assert (
        "Are you sure you would like to delete your collection of assignments?"
        in browser.page_source
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
    assert any(
        h2.text == "Browse Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # assure collection has been deleted
    assert browser.current_url.endswith("collection/list/")
    assert description not in browser.page_source
    # go to featured list view
    browser.find_element_by_link_text("Featured").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Featured Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # go to personal list view
    browser.find_element_by_link_text("Owned").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Your Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # go to followed list view
    browser.find_element_by_link_text("Followed").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Your Followed Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # go to general list view
    browser.find_element_by_link_text("All").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Browse Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )


def collection_buttons(
    browser, assert_, teacher, group, student_group_assignment
):
    # access group from teacher detail page
    browser.find_element_by_link_text("Back to My Account").click()
    browser.find_element_by_id("groups-section").click()
    browser.find_element_by_class_name("md-36").click()
    # open assignment foldable and add assignments to collection
    browser.find_element_by_xpath("//h2[@id='assignments-title']").click()
    browser.find_element_by_id("collection-select").click()
    # assure user is on update view
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "collection-update-form"))
    )

    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Edit Your Collection"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    assert (
        "Please use this page to edit your collection of assignments."
        in browser.page_source
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
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "obj.desc"))
    )

    assert "Collection Statistics" in browser.page_source
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    # click on heart
    browser.find_element_by_class_name("mdc-icon-toggle").click()
    # go back to teacher detail page
    browser.find_element_by_link_text("Back to My Account").click()
    # open collections foldable
    browser.find_element_by_id("collection-section").click()
    # go to followed collections list view
    browser.find_element_by_link_text("Followed Collections").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Your Followed Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # assure that collection is displayed in list view
    assert description in browser.page_source
    # click on collection card
    browser.find_element_by_class_name("mdc-typography--title").click()
    # assure user is on detail view
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "obj.desc"))
    )

    assert "Collection Statistics" in browser.page_source
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    # click on heart
    browser.find_element_by_class_name("mdc-icon-toggle").click()
    # click on view collections
    browser.find_element_by_link_text("View Collections").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Browse Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # assure that collection is displayed in list view
    assert description in browser.page_source
    # go to followed collections list view
    browser.find_element_by_link_text("Followed").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Your Followed Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # assure that collection is not displayed in list view
    assert description not in browser.page_source
    # go to general list view
    browser.find_element_by_link_text("Owned").click()
    # assure user is on list view
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    assert any(
        h2.text == "Your Collections"
        for h2 in browser.find_elements_by_tag_name("h2")
    )

    # assure that collection is displayed in list view
    assert description in browser.page_source
    # click on collection card
    browser.find_element_by_class_name("mdc-typography--title").click()
    # assure user is on detail view
    WebDriverWait(browser, timeout).until(
        presence_of_element_located((By.ID, "obj.desc"))
    )

    assert "Collection Statistics" in browser.page_source
    assert "Collections" in browser.find_element_by_tag_name("h1").text
    # click on assign button
    browser.find_element_by_class_name("collection-distribute").click()
    # assure user is on distribute detail view
    assert (
        "Your may assign the this collection to one of your student groups by"
        in browser.find_element_by_tag_name("small").text
    )
    # assure unassign is preselected
    unassign = browser.find_element_by_xpath(
        "//button[contains(.,'Unassign')]"
    )
    assert unassign
    # click on unassign button
    unassign.click()
    # assure button changes to assign
    assert browser.find_element_by_xpath("//button[contains(.,'Assign')]")
    # go to group
    time.sleep(2)
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
    accept_cookies(browser)
    create_collection(browser, assert_, teacher)
    collection_buttons(
        browser, assert_, teacher, group, undistributed_assignment
    )
