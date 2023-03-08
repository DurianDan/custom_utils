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

class SeleniumHelper():
    def __init__(self,logging_path=None,auto_logging_setup=True) -> None:
        self.options = Options()
        self.element_exception = (NoSuchElementException, StaleElementReferenceException)
        self.driver_exception = (WebDriverException, TimeoutException,common.TimeoutException)
        self.network_exception = (NewConnectionError, MaxRetryError)
        self.driver = 0
        self.logging_path = logging_path
        if auto_logging_setup:
            LoggingQuickSetup(logging_file_path=logging_path).minimalConfig()

    def addOptions(self,
                options:iter = {"--headless","--incognito"},
                page_load_strategy:str="none"
                 ) ->None:
        '''
        Add options, before starting driver
        page_load_strategy https://www.selenium.dev/documentation/webdriver/drivers/options/
        --headless : run driver without opening window
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
        Add functions, to running selenium driver
        maximize : maximize window or stay in normal window
        timeout : set limit to the time spent loading a page, raise error after timeout
        '''
        if type(self.driver) != WebDriver:
            raise ValueError("There aren't any running driver window to maximize or to set timeout\nYou can initialize diver using: normalDriver() or forceDriver()")
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
    def normalDriver(self, quit_running_driver:bool=True)-> WebDriver:
        if quit_running_driver: self.quitRunningDriver()
        self.driver = Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options )
        return self.driver 
    def forceDriver(self,
                    vpn_provider:str="nordvpn",
                    quit_running_driver:bool=True,
                    retry:int=10,
                    retry_interval:int=1
                    ):
        '''
        `vpn_provider` can be one of "hotspotshield"|"nordvpn"|"protonvpn"\n
        `retry` number of retries if the driver can't start\n
        `retry_interval` seconds wait each retry
        '''
        if quit_running_driver: self.quitRunningDriver()
        retry_record = 0
        for i in range(retry):
            try:
                return self.normalDriver()
            except self.driver_exception as e:
                retry_record += 1
                time.sleep(retry_interval)
                logging.ERROR(f"forceDriver(): re-opening driver for the {retry_record} time(s): {e}")
                logging.INFO(VPN_helper(vpn_provider=vpn_provider).autoConnect())
            
