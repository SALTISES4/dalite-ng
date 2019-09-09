from faker import Faker
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from functional_tests.fixtures import *  # noqa
from .utils import accept_cookies, go_to_account, login

fake = Faker()


def create_category(browser, assert_):
    browser.find_element_by_id("question-section").click()
    browser.find_element_by_link_text("Create new").click()

    browser.find_element_by_id("show_category_form").click()

    browser.wait_for(
        lambda: assert_(
            "Enter the name of a new question category." in browser.page_source
        )
    )

    input = browser.find_element_by_xpath(
        "//div[@id='create_new_category']/input[@id='id_title']"
    )
    # ENTER on a blank field throws form error
    input.send_keys(Keys.ENTER)
    browser.wait_for(
        lambda: assert_("This field is required" in browser.page_source)
    )

    # New category is accepted and switches to select form
    time.sleep(1)
    input = browser.find_element_by_xpath(
        "//div[@id='create_new_category']/input[@id='id_title']"
    )
    input.send_keys("Fun new category")
    input.send_keys(Keys.ENTER)
    input = browser.find_element_by_id("autofill_categories")
    input.send_keys(Keys.ENTER)

    assert (
        "Fun new category"
        in browser.find_element_by_id("current_categories").text
    )

    # Clicking chip removes category
    browser.find_element_by_xpath(
        "//div[@id='current_categories']/div[@v='1']"
    ).click()
    browser.wait_for(
        lambda: assert_(
            "Fun new category"
            not in browser.find_element_by_id("current_categories").text
        )
    )

    # Adding existing category throws error
    browser.find_element_by_id("show_category_form").click()
    input = browser.find_element_by_xpath(
        "//div[@id='create_new_category']/input[@id='id_title']"
    )
    input.send_keys("Fun new category")
    input.send_keys(Keys.ENTER)

    browser.wait_for(
        lambda: assert_(
            "Category with this Category Name already exists."
            in browser.find_element_by_id("current_categories").text
        )
    )

    # Cancel works
    time.sleep(1)
    cancel = browser.find_element_by_id("clear_category_form").click()
    browser.wait_for(
        lambda: assert_(
            "Type to search and select at least one category for this "
            "question. You can select multiple categories."
            in browser.page_source
        )
    )

    # Put it back
    input = browser.find_element_by_id("autofill_categories")
    input.send_keys("Fun new category")
    time.sleep(1)
    input.send_keys(Keys.ENTER)

    browser.wait_for(
        lambda: assert_(
            "Fun new category"
            in browser.find_elements_by_class_name("mdc-chip")
        )
    )


def create_discipline(browser, assert_):
    browser.find_element_by_id("question-section").click()
    browser.find_element_by_link_text("Create new").click()

    browser.find_element_by_id("show_discipline_form").click()

    browser.wait_for(
        lambda: assert_(
            "Enter the name of a new discipline." in browser.page_source
        )
    )

    input = browser.find_element_by_xpath(
        "//div[@id='discipline_create_form']/input[@id='id_title']"
    )
    # ENTER on a blank field throws form error
    input.send_keys(Keys.ENTER)
    browser.wait_for(
        lambda: assert_("This field is required" in browser.page_source)
    )

    # New discipline is accepted and switches to select form
    time.sleep(1)
    input = browser.find_element_by_xpath(
        "//div[@id='discipline_create_form']/input[@id='id_title']"
    )
    input.send_keys("Fun new discipline")
    browser.find_element_by_id("submit_discipline_form").click()
    input = browser.find_element_by_id("id_discipline")

    assert "Fun new discipline" in input.text


# def create_assignment(browser, category, discipline):
#     # Teacher can create an assignment
#     browser.get(live_server_url + reverse("teacher", kwargs={"pk": 1}))
#     browser.find_element_by_id("assignment-section").click()
#     browser.find_element_by_link_text("Manage assignments").click()
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#             (By.XPATH, "//h2[contains(text(), 'Create a new assignment')]")
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     inputbox = browser.find_element_by_id("id_identifier")
#     inputbox.send_keys("new-unique-assignment-identifier")
#
#     inputbox = browser.find_element_by_id("id_title")
#     inputbox.send_keys("New assignment title")
#
#     inputbox.submit()
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#                 (
#                     By.XPATH,
#                     "//*[contains(text(), "
#                     "'new-unique-assignment-identifier')]",
#                 )
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     assert (
#         Assignment.objects.filter(
#             identifier="new-unique-assignment-identifier"
#         ).count()
#         == 1
#     )
#
#     # Teacher can edit an assignment
#
#     # Teacher can create a blink assignment
#
#     # Teacher can delete a blink assignment
#
#     # Teacher can edit a blink assignment
#
#     # Access account from link in top right corner
#
#     # Teacher cannot access other teacher accounts
#     browser.get(live_server_url + reverse("teacher", kwargs={"pk": 2}))
#     assert "Forbidden" in browser.page_source
#
#     # Teacher declines TOS
#
#     # Checkout what answer choice form looks like if student answers
#
#     # Teacher cannot delete any questions
#
#     # Need a test to assert reset question never appears in LTI
#
#     # Teacher clones: check new and old question states including
#     # answer_choices
#
#
# def edit_question(browser):
#     # Teacher can edit their questions
#     try:
#         WebDriverWait(browser, timeout).until(
#             element_to_be_clickable((By.ID, "question-section"))
#         ).click()
#     except TimeoutException:
#         assert False
#     question = Question.objects.get(title="Test title")
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             element_to_be_clickable(
#                 (By.ID, "edit-question-{}".format(question.id))
#             )
#         ).click()
#     except TimeoutException:
#         assert False
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#                 (By.XPATH, "//h2[contains(text(), 'Step 1')]")
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     assert "Step 1" in browser.find_element_by_tag_name("h2").text
#
#     tinymce_embed = browser.find_element_by_tag_name("iframe")
#     browser.switch_to.frame(tinymce_embed)
#     ifrinputbox = browser.find_element_by_id("tinymce")
#     ifrinputbox.send_keys("Edited: ")
#     browser.switch_to.default_content()
#
#     inputbox = browser.find_element_by_id("id_title")
#     inputbox.submit()
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#                 (By.XPATH, "//h2[contains(text(), 'Step 2')]")
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     question.refresh_from_db()
#
#     assert "Edited: Test text" in question.text
#
#     # Teacher cannot edit another teacher's questions
#     browser.get(
#         live_server_url + reverse("question-update", kwargs={"pk": 43})
#     )
#     assert "Forbidden" in browser.page_source


def create_PI_question(
    browser, assert_, category, discipline, quality_criterion, assignment
):
    # Teacher can create a question
    # -----------------------------
    browser.find_element_by_id("question-section").click()
    browser.find_element_by_link_text("Create new").click()

    # Step 1
    # ------
    assert "Question" in browser.find_element_by_tag_name("h1").text
    assert "Step 1" in browser.find_element_by_tag_name("h2").text

    # Title
    title = fake.sentence(nb_words=4)
    inputbox = browser.find_element_by_id("id_title")
    inputbox.send_keys(title)

    # Text
    tinymce_embed = browser.find_element_by_tag_name("iframe")
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys(
        fake.paragraph(nb_sentences=8, variable_nb_sentences=False)
    )
    browser.switch_to.default_content()

    # Discipline
    Select(browser.find_element_by_id("id_discipline")).select_by_value("1")

    # Category
    input_category = browser.find_element_by_id("autofill_categories")
    input_category.send_keys(category.title)
    time.sleep(1)
    input_category.send_keys(Keys.ENTER)

    browser.find_element_by_id("question-create-form").submit()

    # Step 2
    # ------
    assert "Step 2" in browser.find_element_by_tag_name("h2").text

    tinymce_embed = browser.find_element_by_id(
        "id_answerchoice_set-0-text_ifr"
    )
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys(fake.sentence(nb_words=10))
    browser.switch_to.default_content()

    tinymce_embed = browser.find_element_by_id(
        "id_answerchoice_set-1-text_ifr"
    )
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys(fake.sentence(nb_words=10))
    browser.switch_to.default_content()

    tinymce_embed = browser.find_element_by_id(
        "id_answerchoice_set-2-text_ifr"
    )
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys(fake.sentence(nb_words=10))
    browser.switch_to.default_content()

    browser.find_element_by_id("id_answerchoice_set-0-correct").click()
    browser.find_element_by_id("id_answerchoice_set-1-correct").click()

    inputbox = browser.find_element_by_id("answer-choice-form")

    inputbox.submit()

    # Step 3
    # ------
    assert "Step 3" in browser.find_element_by_tag_name("h2").text

    browser.find_element_by_id("id_first_answer_choice_0").click()

    # Low quality throws error
    rationale = browser.find_element_by_id("id_rationale")
    rationale.send_keys("Two words.")

    browser.find_element_by_id("answer-form").click()

    error = browser.find_elements_by_class_name("errorlist")[0]
    assert (
        "That does not seem like a clear explanation of your reasoning"
        in error.text
    )
    assert "Expert rationale saved" not in browser.page_source

    browser.find_element_by_id("id_first_answer_choice_0").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.clear()
    rationale.send_keys("This is an expert rationale for answer choice A.")

    browser.find_element_by_id("answer-form").click()

    browser.wait_for(
        lambda: assert_("Expert rationale saved" in browser.page_source)
    )

    browser.find_element_by_id("clear_message").click()
    assert "Expert rationale saved" not in browser.page_source

    # Check minimum number of rationales entered
    assert (
        "You must submit some at least one expert rationale for each "
        "of the correct answer choices above" in browser.page_source
    )

    # Enter another for A
    # FIXME: Why is sleep required here to avoid a stale element error?
    time.sleep(1)
    browser.find_element_by_id("id_first_answer_choice_0").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.clear()
    rationale.send_keys(
        "This is another expert rationale for answer choice A."
    )

    browser.find_element_by_id("answer-form").click()

    # Check minimum number of rationales entered
    browser.wait_for(
        lambda: assert_(
            "You must submit some at least one expert rationale for each "
            "of the correct answer choices above" in browser.page_source
        )
    )

    # FIXME
    time.sleep(1)
    browser.find_element_by_id("id_first_answer_choice_1").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.send_keys("This is an expert rationale for answer choice B.")

    browser.find_element_by_id("answer-form").click()

    browser.wait_for(
        lambda: assert_("Expert rationale saved" in browser.page_source)
    )

    # FIXME
    time.sleep(1)
    browser.find_element_by_id("back").click()

    # Nav buttons work
    assert "Step 2" in browser.find_element_by_tag_name("h2").text

    browser.find_element_by_id("answer-choice-form").submit()

    assert "Step 3" in browser.find_element_by_tag_name("h2").text

    browser.wait_for(
        lambda: assert_(
            "This is an expert rationale for answer choice A."
            in browser.page_source
            and "This is another expert rationale for answer choice A."
            in browser.page_source
            and "This is an expert rationale for answer choice B."
            in browser.page_source
        )
    )

    # Access expert rationale update page and return > no change
    browser.find_elements_by_class_name("click-to-edit")[0].click()

    assert (
        "Approve Expert Rationale"
        in browser.find_elements_by_tag_name("h2")[0].text
    )

    browser.find_element_by_id("update-button").click()

    browser.wait_for(
        lambda: assert_(
            "This is an expert rationale for answer choice A."
            in browser.page_source
            and "This is another expert rationale for answer choice A."
            in browser.page_source
            and "This is an expert rationale for answer choice B."
            in browser.page_source
        )
    )

    # Remove expert rationale for B and return > gone and min rationale error
    browser.find_elements_by_class_name("click-to-edit")[2].click()

    browser.find_element_by_id("id_expert").click()

    browser.find_element_by_id("update-button").click()

    browser.wait_for(
        lambda: assert_(
            "This is an expert rationale for answer choice A."
            in browser.page_source
            and "This is another expert rationale for answer choice A."
            in browser.page_source
        )
    )

    browser.wait_for(
        assert_(
            "You must submit some at least one expert rationale for each "
            "of the correct answer choices above" in browser.page_source
        )
    )

    assert (
        "This is an expert rationale for answer choice B."
        not in browser.page_source
    )

    # FIXME
    time.sleep(1)
    browser.find_element_by_id("id_first_answer_choice_1").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.send_keys(
        "This is another expert rationale for answer choice B."
    )

    browser.find_element_by_id("answer-form").click()

    browser.wait_for(
        lambda: assert_("Expert rationale saved" in browser.page_source)
    )

    browser.find_element_by_id("next").click()

    # Step 4
    # ------
    # Check nav buttons
    browser.find_element_by_id("back").click()

    assert "Step 3" in browser.find_elements_by_tag_name("h2")[0].text

    browser.find_element_by_id("next").click()

    # Add low quality sample rationale
    assert "Step 4" in browser.find_elements_by_tag_name("h2")[0].text

    browser.find_element_by_id("id_first_answer_choice_0").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.send_keys("Short rationale.")

    browser.find_element_by_id("answer-form").click()

    # FIXME
    time.sleep(1)
    error = browser.find_elements_by_class_name("errorlist")[0]
    assert (
        "That does not seem like a clear explanation of your reasoning"
        in error.text
    )
    assert "Sample answer saved" not in browser.page_source

    browser.find_element_by_id("id_first_answer_choice_0").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.clear()
    rationale.send_keys("This is an acceptable sample answer.")

    browser.find_element_by_id("answer-form").click()
    browser.wait_for(
        assert_(lambda: "Sample answer saved" in browser.page_source)
    )

    # FIXME
    time.sleep(1)
    error = browser.find_elements_by_class_name("errorlist")[0]
    assert (
        "You must submit some at least one example rationale for each of the answer choices above"  # noqa
        in error.text
    )

    # FIXME
    time.sleep(1)
    browser.find_element_by_id("id_first_answer_choice_1").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.clear()
    rationale.send_keys("This is an acceptable sample answer.")

    browser.find_element_by_id("answer-form").click()
    browser.wait_for(
        assert_(lambda: "Sample answer saved" in browser.page_source)
    )

    # FIXME
    time.sleep(1)
    error = browser.find_elements_by_class_name("errorlist")[0]
    assert (
        "You must submit some at least one example rationale for each of the answer choices above"  # noqa
        in error.text
    )

    # FIXME
    time.sleep(1)
    browser.find_element_by_id("id_first_answer_choice_2").click()

    rationale = browser.find_element_by_id("id_rationale")
    rationale.clear()
    rationale.send_keys("This is an acceptable sample answer.")

    browser.find_element_by_id("answer-form").click()
    browser.wait_for(
        assert_(lambda: "Sample answer saved" in browser.page_source)
    )

    # FIXME
    time.sleep(1)
    browser.find_element_by_id("clear_message").click()
    assert "Sample answer saved" not in browser.page_source

    # Use auto add feature
    Select(browser.find_element_by_id("id_assignments")).select_by_value(
        assignment.identifier
    )

    # Save
    done = browser.find_element_by_id("done").click()
    assert "My Account" in browser.find_elements_by_tag_name("h1")[0].text

    # New question in their list of questions
    browser.find_element_by_id("question-section").click()
    browser.wait_for(assert_(lambda: title in browser.page_source))

    # Check for question in assignment
    browser.find_element_by_id("assignment-section").click()
    browser.find_element_by_link_text(assignment.identifier).click()

    assert assignment.title in browser.find_elements_by_tag_name("h1")[0].text


def edit_PI_question():
    pass

    # Access question edit prior to student answers existing

    # Access question edit post student answers existing


def create_RO_question(browser, assert_, category, discipline, teacher):
    browser.find_element_by_id("question-section").click()
    browser.find_element_by_link_text("Create new").click()

    # Step 1
    # ------
    assert "Question" in browser.find_element_by_tag_name("h1").text
    assert "Step 1" in browser.find_element_by_tag_name("h2").text

    # Title
    title = fake.sentence(nb_words=4)
    inputbox = browser.find_element_by_id("id_title")
    inputbox.send_keys(title)

    # Text
    tinymce_embed = browser.find_element_by_tag_name("iframe")
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys(
        fake.paragraph(nb_sentences=8, variable_nb_sentences=False)
    )
    browser.switch_to.default_content()

    # Discipline
    Select(browser.find_element_by_id("id_discipline")).select_by_value("1")

    # Category
    input_category = browser.find_element_by_id("autofill_categories")
    input_category.send_keys(category.title)
    time.sleep(1)
    input_category.send_keys(Keys.ENTER)

    # Switch PI --> RO
    Select(browser.find_element_by_id("id_type")).select_by_value("RO")

    browser.wait_for(
        lambda: assert_(
            "Add fake attributions" not in browser.page_source
            and "Sequential rationale review" not in browser.page_source
            and "Rationale selection algorithm" not in browser.page_source
            and "Grading scheme" not in browser.page_source
        )
    )

    browser.find_element_by_id("question-create-form").submit()

    # Step 2
    # ------
    assert "Step 2: Preview" in browser.find_element_by_tag_name("h2").text

    browser.find_element_by_id("back").submit()
    assert "Step 1" in browser.find_element_by_tag_name("h2").text

    browser.find_element_by_id("question-create-form").submit()
    assert "Step 2: Preview" in browser.find_element_by_tag_name("h2").text

    browser.find_element_by_id("back").submit()
    browser.find_element_by_id("next").submit()
    assert "Step 2: Preview" in browser.find_element_by_tag_name("h2").text
    assert (
        "You currently do not have any assignments. "
        "You can create one from your account page."
        in browser.find_element_by_id("add_question_to_assignment").text
    )

    browser.find_element_by_id("done").click()

    assert "My Account" in browser.find_element_by_tag_name("h1").text

    # New question in their list of questions
    browser.find_element_by_id("question-section").click()
    browser.wait_for(assert_(lambda: title in browser.page_source))


def edit_RO_question():
    pass

    # Access question edit prior to student answers existing

    # Access question edit post student answers existing


def test_create_category(browser, assert_, teacher):
    login(browser, teacher)
    accept_cookies(browser)
    go_to_account(browser)
    create_category(browser, assert_)


def test_create_discipline(browser, assert_, teacher):
    login(browser, teacher)
    accept_cookies(browser)
    go_to_account(browser)
    create_discipline(browser, assert_)


def test_create_PI_question(
    browser,
    assert_,
    category,
    discipline,
    teacher,
    quality_min_words,
    assignment,
):
    teacher.assignments.add(assignment)
    assignment.owner.add(teacher.user)
    login(browser, teacher)
    accept_cookies(browser)
    go_to_account(browser)
    create_PI_question(
        browser, assert_, category, discipline, quality_min_words, assignment
    )
    edit_PI_question()


def test_create_RO_question(browser, assert_, category, discipline, teacher):
    login(browser, teacher)
    accept_cookies(browser)
    go_to_account(browser)
    create_RO_question(browser, assert_, category, discipline, teacher)
    edit_RO_question()


def test_clone_PI_question():
    pass


def test_clone_RO_question():
    pass
