from selenium.webdriver import Remote, ChromeOptions

# type casting in the function
from selenium.webdriver.chrome.webdriver import WebDriver
from typing import Literal, Tuple

# Error handling
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException,
)
from selenium import common
from urllib3.exceptions import NewConnectionError, MaxRetryError

# wait seconds between retry
import time


class SeleniumHelper:
    def __init__(
        self,
        command_executor: str | None = None,
        driver: WebDriver | None = None,
    ) -> None:
        self.options = ChromeOptions()
        if driver:
            self.driver = driver
            self.command_executor = driver.command_executor._url
        elif command_executor:
            self.command_executor = command_executor
            self.driver: WebDriver | None = None
        else:
            raise ValueError(
                "Either `command_executor` or `driver` argument needs to be parsed"
            )

        self.element_exception: Tuple[Exception, ...] = (
            NoSuchElementException,
            StaleElementReferenceException,
        )
        self.driver_exception: Tuple[Exception, ...] = (
            WebDriverException,
            TimeoutException,
            common.TimeoutException,
        )
        self.network_exception: Tuple[Exception, ...] = (
            NewConnectionError,
            MaxRetryError,
        )

    def log(
        self, msg: str, type: Literal["warning", "error", "info"] = "info"
    ) -> None:
        print(f"SeleniumHelper: {type}: {msg}")

    def check_driver(self):
        checks = {  # for future checks
            "driverExist": type(self.driver) == WebDriver,
        }

        if not checks["driverExist"]:
            self.log("There isn't any running driver", "error")
        return checks

    def add_options(
        self,
        arguments: list = ["--incognito"],
        page_load_strategy: str = "none",
    ) -> None:
        """
        Add `arguments`, before starting driver\n
        `page_load_strategy` https://www.selenium.dev/documentation/webdriver/drivers/options/\n
            --headless : run driver without opening window\n
            --incognito : run driver in incognito mode
        """
        # add options
        if self.check_driver()["driverExist"]:
            raise ValueError(f"")
        for op in arguments:
            self.options.add_argument(op)
            self.log(f"Driver will perform option: {op}")
        self.log(f"Driver will have page_load_strategy: {page_load_strategy}")
        self.options.page_load_strategy = page_load_strategy

    def add_functions(
        self,
        maximize: bool = True,
        timeout=None,
    ) -> None:
        """
        Add functions, to running selenium driver\n
        maximize : maximize window or stay in normal window\n
        timeout : set limit to the time spent loading a page, raise error after timeout
        """
        if type(self.driver) != WebDriver:
            raise ValueError(
                "There aren't any running-driver to maximize window or to set timeout\nYou can initialize diver using: normalCreateDriver() or forceCreateDriver()"
            )
        if maximize:
            self.driver.maximize_window()
        if type(timeout) == int and timeout > 0:
            self.driver.set_page_load_timeout(timeout)

    def get_error_msg(self, error: Exception) -> str:
        for msg_field in ["message", "msg"]:
            if hasattr(error, msg_field):
                return getattr(error, msg_field)
        return str(error)

    def quit_running_driver(self):
        """
        Quit any running driver
        """
        if type(self.driver) == WebDriver:
            try:
                self.driver.quit()
            except Exception as err:
                self.log(
                    "quitRunningDriver(): error while quitting driver:\n",
                    "warning",
                )
                self.log(self.get_error_msg(err), "warning")
            self.driver = 0
            self.log(
                "Driver has quit, and the variable 'driver' is now of type 'int', containing value 0",
                "warning",
            )
        else:
            self.log("There isn't any running driver to quit()", "warning")

    def normal_create_driver(
        self, command_executor: str, quit_running_driver: bool = True
    ) -> WebDriver:
        """Create chrome driver, controlling a remote-debug selenium grid chrome browser

        ## Parameters
        :param command_executor: the url to the remote selenium grid. E.g.: http://192.21.11.10:4444
        :param quit_running_driver: if `True`, then terminate the running driver
        """
        if quit_running_driver:
            self.quit_running_driver()

        driver: WebDriver = Remote(
            command_executor=command_executor, options=self.options
        )
        return driver

    def force_create_driver(
        self,
        quit_running_driver: bool = True,
        retry: int = 10,
        retry_interval: int = 1,
    ):
        retry_record = 0
        last_err = ""
        for _ in range(retry):
            try:
                return self.normal_create_driver(
                    quit_running_driver=quit_running_driver
                )
            except self.driver_exception as err:
                last_err = str(err)
                retry_record += 1
                time.sleep(retry_interval)
                self.log(
                    f"forceCreateDriver(): re-opening driver for the {retry_record} time(s): {err}",
                    "warning",
                )
        raise ValueError(
            f"Can't start driver after {retry} retries, last error was {last_err}"
        )
