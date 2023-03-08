from selenium.webdriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# type casting in the function
from selenium.webdriver.chrome.webdriver import WebDriver 
# Error handling
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException,WebDriverException, TimeoutException
from selenium import common
from urllib3.exceptions import NewConnectionError, MaxRetryError

# logging
from Debug import LoggingQuickSetup,logging

#change VPN
from VPN import VPN_helper

# wait seconds between retry 
import time

class seleniumHelper():
    def __init__(self,logging_path=None,auto_logging_setup=True) -> None:
        self.options = Options()
        self.element_exception = {NoSuchElementException, StaleElementReferenceException}
        self.driver_exception = {WebDriverException, TimeoutException,common.TimeoutException}
        self.network_exception = {NewConnectionError, MaxRetryError}
        self.driver = 0
        self.logging_path = logging_path
        if auto_logging_setup:
            LoggingQuickSetup(logging_file_path=logging_path).minimalConfig()

    def checkDriver(self):
        checks = { # for future checks
            "driverExist": type(self.driver) == WebDriver,
        }

        if not checks["driverExist"]:
            logging.ERROR("There isn't any running driver")
        return checks
    
    def addOptions(self,
                options:iter = {"--headless","--incognito"},
                page_load_strategy:str="none"
                 ) ->None:
        '''
        Add options, before starting driver\n
        page_load_strategy https://www.selenium.dev/documentation/webdriver/drivers/options/\n
        --headless : run driver without opening window\n
        --incognito : run driver in incognito mode
        '''
        # add options
        for op in options:
            self.options.add_argument(op)
            logging.INFO(f"Driver will perform option: {op}")
        logging.INFO(f"Driver will have page_load_strategy: {page_load_strategy}")
        self.options.page_load_strategy = page_load_strategy
    
    def addFunctions(self,
                maximize:bool=True,
                timeout = None,
                 ) ->None:
        '''
        Add functions, to running selenium driver\n
        maximize : maximize window or stay in normal window\n
        timeout : set limit to the time spent loading a page, raise error after timeout
        '''
        if type(self.driver) != WebDriver:
            raise ValueError("There aren't any running-driver to maximize window or to set timeout\nYou can initialize diver using: normalDriver() or forceDriver()")
        if maximize:
            logging.INFO()
            self.driver.maximize_window()
        if (type(timeout) == int and timeout > 0):
            self.driver.set_page_load_timeout (timeout)

    def quitRunningDriver(self):
        '''
        Quit any running driver
        '''
        if type(self.driver) == WebDriver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.WARNING(f"quitRunningDriver(): {e}")
        else:
            logging.WARNING("There isn't any running driver to quit()")
    def normalDriver(self, quit_running_driver:bool=True)-> WebDriver:
        if quit_running_driver: self.quitRunningDriver()
        self.driver = Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options )
        return self.driver 
    def forceDriver(self,
                    vpn_provider:str="nordvpn",
                    reconnect_vpn:bool=True,
                    quit_running_driver:bool=True,
                    retry:int=10,
                    retry_interval:int=1
                    ):
        '''
        `vpn_provider` can be one of "hotspotshield"|"nordvpn"|"protonvpn"\n
            if `vpn_provider` is empty `""`, vpn will not be reset
        `retry` number of retries if the driver can't start\n
        `retry_interval` seconds wait each retry
        '''
        self.vpn_provider = vpn_provider
        if quit_running_driver: self.quitRunningDriver()
        retry_record = 0
        last_err = ""
        for _ in range(retry):
            try:
                return self.normalDriver()
            except self.driver_exception as err:
                last_err = str(err)
                retry_record += 1
                time.sleep(retry_interval)
                logging.ERROR(f"forceDriver(): re-opening driver for the {retry_record} time(s): {err}")
                if reconnect_vpn:
                    logging.INFO(VPN_helper(vpn_provider=vpn_provider).autoConnect())
        
        raise ValueError(f"Can't start driver after {retry} retries, last error was {last_err}")

class driverHelper(seleniumHelper):
    def __init__(self, logging_path=None, auto_logging_setup=True) -> None:
        super().__init__(logging_path, auto_logging_setup)
    
    def reopenDriver(self, retry_count:int=1,reconnect_vpn:bool=True ):
        '''
        `retry_count` is the times that the driver has been quit and reopen,
        this argument is only for `logging`
        '''
        self.quitRunningDriver()
        self.driver.quit()
        logging.WARNING(f"Reopening driver for the {retry_count} time(s)")
        self.forceDriver(reconnect_vpn=reconnect_vpn)
    
    def forceFindElement(self,
                     by:str=By.XPATH|By.CLASS_NAME|By.ID|By.CSS_SELECTOR,
                     element_string:str | None = None,
                     retry:int=10,
                     retry_interval:int=1,
                     ):
        '''
        Retry until getting the element\n
        `elment_string` : E.g. "./html/body/div\n
        `by` : Method for the driver to get the elemen\n
        `retry` : number of retries\n
        `retry_interval` : Seconds between each retry\n
        if `vpn_provider` is not empty (empty by default), `forceFindElement()` will change vpn after each retry   
        '''
        if not self.checkDriver()["driverExist"]:
            raise ValueError("Can't find element without a proper driver")
        
        retry_record = 0
        last_err = ""
        for _ in range(retry):
            try:
                return self.driver.find_element(by=by, value=element_string)
            except self.element_exception as err:
                last_err = str(err)
                retry_record += 1
                logging.ERROR(f"Retrying getting element for the {retry_record} time(s)")
                time.sleep(retry_interval)
                if self.vpn_provider != "":
                    logging.WARNING(
                        VPN_helper(vpn_provider=self.vpn_provider).autoConnect()
                    )
            except self.driver_exception as err:
                last_err = str(err)
                self.reopenDriver(reconnect_vpn=False,retry_count=retry_record)
            except self.network_exception as err:
                last_err = str(err)
                self.reopenDriver(reconnect_vpn=True,retry_count=retry_record)
        raise ValueError(f"Cant find the element after {retry_record} retries, last error was {last_err}")