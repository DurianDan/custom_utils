from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from selenium_helper import SeleniumHelper

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

# type hinting in the function
from selenium.webdriver.remote.webelement import WebElement

# wait seconds between retry
import time
from functools import wraps
from typing import Callable, Any, List, Literal



class DriverHelper(SeleniumHelper):
    def __init__(
        self,
        command_executor: str | None = None,
        driver: WebDriver | None = None,
    ) -> None:
        super().__init__(command_executor, driver)

    def reopen_driver(self, retry_count: int = 1, reconnect_vpn: bool = True):
        """
        `retry_count` is the times that the driver has been quit and reopen,
        this argument is only for `logging`
        """
        self.quit_running_driver()
        self.log(f"Reopening driver for the {retry_count} time(s)", "warning")
        self.force_create_driver(reconnect_vpn=reconnect_vpn)

    def selenium_try_loop(selenium_fn: Callable) -> Any:
        @wraps(selenium_fn)
        def wrapper(self, *args, **kwargs):
            last_err: Exception | None = None
            for refresh in range(1, 4):
                for wait in range(1, 6):
                    try:
                        result = selenium_fn(self, *args, **kwargs)
                        return result
                    except Exception as err:
                        print(
                            err.message if hasattr(err, "message") else str(err)
                        )
                        print(f"Sleeping for {wait} second(s)")
                        last_err = err
                        time.sleep(wait)
                print(f"Refresh page for the {refresh} time")
                self.driver.refresh()
            raise last_err

        return wrapper

    def find_altered_elements(
        self, element, alternative_element
    ) -> List[WebElement]:
        results = self.driver.find_elements(*element)
        if not results:
            results = self.driver.find_elements(*alternative_element)
        return results

    @selenium_try_loop
    def check_element_loaded(self, element, altered_element=None) -> None:
        if altered_element:
            self.find_altered_element(element, altered_element)
        else:
            self.driver.find_element(*element)

    def force_find_element(
        self,
        method: By,
        selector: str,
        element_as_finder: WebElement = None,
        retry: int = 5,
        retry_interval: int = 1,
        find_element_message: str = None,
        default_value: Any | None | Literal["None"] = None,
    ):
        """
        Retry until getting the element\n

        ## Parameter
        :param selector: E.g. "./html/body/div\n
        :param method: Method for the driver to get the element: \n
        :param retry: number of retries\n
        :param element_as_finder: using an element to find sub-element, instead of driver\n
        :param retry_interval: Seconds between each retry\n
        :param default_value: if set, will return the `default_value` if the element cant be found after many retry. If you want to return `None`, parse the string "None".
        """
        self.check_driver()["driverExist"]

        retry_record = 0
        last_err = ""
        if find_element_message:
            self.log(f"Trying to get the element {selector}")

        for trying in range(retry):
            try:
                if type(element_as_finder) == WebElement:
                    return element_as_finder.find_element(
                        by=method, value=selector
                    )
                else:
                    return self.driver.find_element(by=method, value=selector)

            except self.element_exception as err:
                last_err = err
                if trying == int(retry / 2):
                    self.driver.refresh()
                    time.sleep(int(retry / 2))
                pass
            except self.driver_exception as err:
                last_err = err
                self.reopen_driver(retry_count=retry_record)
            except self.network_exception as err:
                last_err = err
                self.reopen_driver(retry_count=retry_record)
            retry_record += 1
            self.log(
                f"Retrying getting element for the {retry_record} time(s), while handling this error :{last_err}",
                "error",
            )
            time.sleep(retry_interval)
        self.log(
            f"Cant find element {method}:{selector}, after {retry_record} retries",
            "warning",
        )

        if default_value:
            return None if default_value == "None" else default_value
        raise ValueError(f"Last error was {last_err}")

    def force_get(
        self,
        url: str,
        try_refresh_before_retry: bool = False,
        retry: int = 4,
        retry_interval: int | Literal["incremental"] = 1,
        try_reopen_driver: bool = True,
        log: bool | str = True,
    ):
        """Retry until the driver can access the desired `url`

        Parameters
        ---
        :param `try_refresh_before_retry`: if set to `True`, driver will refresh page before atempting reopen the whole driver,\nif the desired url is available after refresh, helper won't reopen driver\n
        :param `retry`: is the number of retries
        :param `retry_interval`: Seconds wait each retry. If `"incremental"` is parse, the wait seconds will increase by one, after each retry.
        :param `try_reopen_driver`: if `True`, driver will be closed and reopen each retry.
        :param `log`: if `True`, will log to the console the url to which the driver is trying to access. If a string is parsed, it must have an unformated variable inside it named `msg`, the `helper` will input its log message in that variable, E.g.: `"This is my custom logger: {msg}"`
        """
        retry_record = 0
        last_err = ""
        if log:
            log_msg = f"Trying to reach the website {url}"
            if type(log) == str:
                assert (
                    "{msg}" in log
                ), 'The log string must have a unformated variable named `msg`, E.g.: `"This is my custom logger: {msg}"`'
                log_msg = log.format(msg=log_msg)
            self.log(log_msg)

        for _ in range(retry):
            try:
                self.driver.get(url)
                return
            except self.driver_exception + self.network_exception as err:
                last_err = err
                if try_refresh_before_retry:
                    try:
                        self.driver.refresh()
                        return
                    except:
                        self.log("Driver cant refresh", "warning")
                if try_reopen_driver:
                    self.log("Trying reopening driver")
                    self.reopen_driver(
                        reconnect_vpn=True, retry_count=retry_record
                    )
            retry_record += 1
            self.log(
                f"Retrying accessing {url}, for the {retry_record} time(s), while handling whis error :{self.get_error_msg(last_err)}",
                "error",
            )
            time.sleep(retry_interval)
        raise ValueError(
            f"Cant access {url} after {retry_record} retries, last error was {last_err}"
        )
