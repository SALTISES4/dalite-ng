import contextlib
import datetime
import os
import time
from functools import partial

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from selenium import webdriver
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    WebDriverException,
)
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


@pytest.yield_fixture
def browser(live_server):
    staging_server = os.environ.get("STAGING_SERVER")

    if staging_server:
        print(f"Staging server: {staging_server}")
        selenium_hub = os.environ.get("SELENIUM_HUB")
        print(" > Get browser from env")
        browser_name = os.environ.get("BROWSER", "Chrome")
        print(" > Settings options")
        if browser_name.lower() == "chrome":
            options = webdriver.chrome.options.Options()
            options.add_argument("start-maximized")
            options.add_argument("window-size=1080,1440")
            # options.add_argument("auto-open-devtools-for-tabs")

        if browser_name.lower() == "firefox":
            options = webdriver.firefox.options.Options()
            options.add_argument("--width=1080")
            options.add_argument("--height=1440")

        if browser_name.lower() == "edge":
            options = webdriver.edge.options.Options()
            options.add_argument("--width=1080")
            options.add_argument("--height=1440")

        print(" > Requesting remote browser instance from hub")
        driver = webdriver.Remote(
            command_executor=f"http://{selenium_hub}/wd/hub",
            options=options,
        )
        print(f" > Received browser {driver}")

    else:
        raise ImproperlyConfigured(
            "Missing STAGING_SERVER setting in environment"
        )

    @wait
    def wait_for(fn):
        return fn

    driver.wait_for = wait_for

    if browser_name.lower() == "chrome":
        # Add assertion that web console logs are null after any get() or click()
        # Log and screenshot function
        def add_log(fct, driver, *args, **kwargs):
            if WATCH:
                # This "implicit" wait on redirect makes a lot of tests in Chrome pass, but fail in FF and Edge
                # TODO: Refactor tests to explicitly wait for first detected element
                time.sleep(2)

            result = fct(*args, **kwargs)

            logs = driver.get_log("browser")

            try:
                print(f"Logs checked after: {fct.func.__name__}")
            except AttributeError:
                print(f"Logs checked after: {fct.__name__}")

            take_screenshot(driver)

            # Ignore network errors during testing
            filtered_logs = [
                d
                for d in logs
                if d["source"] != "network"
                and d["level"] == "ERROR"
                and "tinymce" not in d["message"]
                and "youtube" not in d["message"]
                and "mdc-auto-init" not in d["message"]
            ]
            assert not filtered_logs, logs

            return result

        # Add screenshot
        def take_screenshot(driver):
            file_path = os.path.join(
                settings.BASE_DIR,
                f"snapshots/test-{datetime.datetime.now()}.png",
            )
            with contextlib.suppress(
                UnexpectedAlertPresentException, WebDriverException
            ):
                driver.save_screenshot(file_path)

        # Log function for finders
        def click_with_log(finder, driver, *args, **kwargs):
            web_element = finder(*args, **kwargs)

            _click = getattr(web_element, "click")

            setattr(web_element, "click", partial(add_log, _click, driver))

            return web_element

        # Update get()
        _get = getattr(driver, "get")
        setattr(driver, "get", partial(add_log, _get, driver))

        # Update find_element() to add logging to click() of passed WebElement
        for method in dir(driver):
            if "find_element_" in method:
                _method = getattr(driver, method)
                if callable(_method):
                    setattr(
                        driver,
                        method,
                        partial(click_with_log, _method, driver),
                    )

    if staging_server:
        driver.server_url = f"http://{staging_server}"
    else:
        driver.server_url = live_server.url

    yield driver
    driver.quit()
    if os.path.exists("geckodriver.log"):
        os.remove("geckodriver.log")


second_browser = browser
