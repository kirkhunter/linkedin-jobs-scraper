from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from client import LIClient
from settings import search_keys
import time




if __name__ == "__main__":

    # initialize selenium webdriver
    driver = webdriver.Chrome()
    driver.get("https://www.linkedin.com/uas/login")

    # initialize LinkedIn web client
    liclient = LIClient(driver, **search_keys)

    liclient.login()

    # wait for page load
    time.sleep(3)

    assert isinstance(search_keys["keywords"], list)
    assert isinstance(search_keys["locations"], list)

    for keyword in search_keys["keywords"]:
        for location in search_keys["locations"]:

            liclient.navigate_to_jobs_page()

            liclient.enter_search_keys(keyword, location)

            liclient.customize_search_results(keyword, location, **search_keys)

            liclient.navigate_search_results(keyword, location)


    liclient.driver_quit()
