# LinkedIn Jobs Scaper

First, I do not condone scraping LinkedIn data in any way. Anyone who wishes to do so should first read LinkedIn's statement on their [prohibition of scraping software](https://www.linkedin.com/help/linkedin/answer/56347/prohibition-of-scraping-software?lang=en).


But if one were to scrape LinkedIn job postings using selenium webdriver with access to premium user insights, say, then this repository serves as a collection of tools that one might find useful. I found the selenium webdriver to be key in this process, as LI dynamically renders their pages with node.js, using a tool like BeautifulSoup will grab the initial JavaScript code but not the data that is displayed on the page. Also, note that LinkedIn actively suspends accounts due to excessive page views.


This module requires python bindings for the selenium webdriver
```bash
pip install selenium
```


Here is a quick demo of how one can use the LinkedIn client and scrape tools.

```python
from selenium import webdriver
from client import LIClient
from settings import search_keys
import time


# initialize Selenium Web Driver
driver = webdriver.Chrome()
driver.get("https://www.linkedin.com/uas/login")

# initialize LinkedIn web client
liclient = LIClient(driver, **search_keys)

liclient.login()

# wait for page load
time.sleep(3)

keyword  = "data analyst"
location = "san francisco bay area"

liclient.navigate_to_jobs_page()

liclient.enter_search_keys(keyword, location)

liclient.customize_search_results(**search_keys)

liclient.navigate_search_results(keyword, location)

liclient.driver_quit()
```

