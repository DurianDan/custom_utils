from selenium.webdriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

driver = Chrome(
    service=Service(ChromeDriverManager().install())
)

driver.get("https://google.com")
print(driver.find_element("xpath","./html/body").text)
driver.quit()

print(type(driver))