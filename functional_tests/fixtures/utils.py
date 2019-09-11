import os
import time
from functools import partial

import pytest
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement


MAX_WAIT = 30
try:
    WATCH = settings.WATCH
except AttributeError:
    WATCH = False


# Wait decorator
def wait(fn):
    def modified_fn(*args, **kwargs):
        start_time = time.time()
        while True:
            try:
                return fn(*args, **kwargs)
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)

    return modified_fn


# wait_for expects a function
@pytest.fixture
def assert_():
    def fct(statement):
        assert statement

    return fct


def create_browser(live_server, browser_id=1, devtools=False):
    if hasattr(settings, "TESTING_BROWSER"):
        browser = settings.TESTING_BROWSER.lower()
    else:
        browser = "firefox"

    options = webdriver.ChromeOptions()
    options.add_experimental_option("w3c", False)
    if devtools:
        options.add_argument("auto-open-devtools-for-tabs")

    if hasattr(settings, "HEADLESS_TESTING") and settings.HEADLESS_TESTING:
        os.environ["MOZ_HEADLESS"] = "1"
        options.add_argument("headless")

    if browser == "firefox":
        try:
            driver = webdriver.Firefox()
        except WebDriverException:
            driver = webdriver.Chrome(options=options)
    elif browser == "chrome":
        try:
            driver = webdriver.Chrome(options=options)
        except WebDriverException:
            driver = webdriver.Firefox()
    else:
        raise ValueError(
            "The TESTING_BROWSER setting in local_settings.py must either be "
            "firefox or chrome."
        )

    # Add an implicit wait function to handle latency in page loads
    @wait
    def wait_for(fn):
        return fn

    driver.wait_for = wait_for
    driver.implicitly_wait(MAX_WAIT)

    # Add assertion that web console logs are null after any get() or click()
    # Log function for get
    def add_log(fct, driver, *args, **kwargs):
        if WATCH:
            time.sleep(1)

        result = fct(*args, **kwargs)

        logs = driver.get_log("browser")

        if isinstance(result, WebElement):
            print("Logs checked after: " + fct.func.__name__)
        else:
            print("Logs checked after: " + fct.__name__)

        # Ignore network errors during testing
        filtered_logs = [
            d
            for d in logs
            if d["source"] != "network"
            and "tinymce" not in d["message"]
            and "mdc-auto-init" not in d["message"]
        ]
        assert len(filtered_logs) == 0, logs

        return result

    # Log function for finders
    def click_with_log(finder, driver, *args, **kwargs):
        web_element = finder(*args, **kwargs)

        _click = getattr(web_element, "click")
        setattr(web_element, "click", partial(add_log, _click, driver))

        return web_element

    # Update get()
    _get = getattr(driver, "get")
    setattr(driver, "get", partial(add_log, _get, driver))

    # Update find_*() to add logging to click() of passed WebElement
    for method in dir(driver):
        if "find_element_" in method:
            _method = getattr(driver, method)
            if callable(_method):
                setattr(
                    driver, method, partial(click_with_log, _method, driver)
                )

    driver.server_url = live_server.url
    return driver


def close_browser(browser):
    browser.close()
    if os.path.exists("geckodriver.log"):
        os.remove("geckodriver.log")


@pytest.yield_fixture
def browser(live_server):
    browser = create_browser(live_server, 1, devtools=False)
    yield browser
    close_browser(browser)


@pytest.yield_fixture
def second_browser(live_server):
    second_browser = create_browser(live_server, 2, devtools=True)
    yield second_browser
    close_browser(second_browser)


@pytest.yield_fixture
def third_browser(live_server):
    third_browser = create_browser(live_server, 3, devtools=True)
    yield third_browser
    close_browser(third_browser)


@pytest.yield_fixture
def fourth_browser(live_server):
    fourth_browser = create_browser(live_server, 4, devtools=True)
    yield fourth_browser
    close_browser(fourth_browser)


@pytest.yield_fixture
def fifth_browser(live_server):
    fifth_browser = create_browser(live_server, 5, devtools=True)
    yield fifth_browser
    close_browser(fifth_browser)
