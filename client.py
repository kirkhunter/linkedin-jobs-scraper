from __future__ import print_function
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrape import *
from settings import search_keys
import datetime
import json
import time




def write_line_to_file(filename, data):
    """
    output the current job title, company, job id, then write
    the scraped data to file
    """

    job_title = data["job_info"]["job_title"]
    company   = data["job_info"]["company"]
    job_id    = data["job_info"]["job_id"]

    message = u"Writing data to file for job listing:"
    message += "\n  {}  {};   job id  {}\n"

    try:
        print(message.format(job_title, company, job_id))
    except Exception as e:
        print("Encountered a unicode encode error while attempting to print " \
                    "the job post information;  job id {}".format(job_id))
        pass

    with open(filename, "a") as f:
        f.write(json.dumps(data) + '\n')


def get_date_time():
    """
    get the full date along with the hour of the search, just for 
    completeness. Allows us to solve for of the original post 
    date.
    """
    now   =  datetime.datetime.now()
    month =  str(now.month) if now.month > 9 else '0' + str(now.month)
    day   =  str(now.day) if now.day > 9 else '0' + str(now.day)
    date  =  ''.join(str(t) for t in [now.year, month, day, now.time().hour])
    return date


def adjust_date_range(driver, date_range):
    """select a specific date range for job postings"""

    if date_range == 'All': return

    index = ['', 'All', '1', '2-7', '8-14', '15-30'].index(date_range)

    button_path = "html/body/div[3]/div/div[2]/div[1]/div[4]/form/div/ul/li" \
                                "[3]/fieldset/button"

    date_path = "html/body/div[3]/div/div[2]/div[1]/div[4]/form/div/ul/li" \
                            "[3]/fieldset/div/ol/li[{}]/div/label".format(index)

    attempts = 1
    while True:
        try:
            elem = driver.find_element_by_xpath(button_path)
            time.sleep(3)
        except Exception as e:
            attempts += 1
            if attempts > 25:
                break
        else:
            elem.click()
            time.sleep(3)
            driver.find_element_by_xpath(date_path).click()
            time.sleep(3)
            break 


def adjust_search_radius(driver, search_radius):
    """
    select the appropriate user-defined search radius from the 
    dropdown window
    """

    if search_radius == '50': return

    distance_selector = "select#advs-distance > option[value='{}']".format(search_radius)

    try:
        driver.find_element_by_css_selector(distance_selector).click()
    except Exception as e:
        print(e)
    else:
        time.sleep(3)
        try:
            driver.find_element_by_css_selector("input.submit-advs").click()
            time.sleep(3)
        except Exception as e:
            print(e)


def adjust_salary_range(driver, salary):
    """adjust the salary range, default is All salaries"""

    if salary == 'All': return

    index = ['', 'All', '40+', '60+', '80+', '100+', 
                        '120+', '160+', '180+', '200+'].index(salary)

    salary_button = "html/body/div[3]/div/div[2]/div[1]/div[4]/form/div/ul/" \
                                    "li[4]/fieldset/button"

    salary_path = "html/body/div[3]/div/div[2]/div[1]/div[4]/form/div/ul/" \
                                "li[4]/fieldset/div[1]/ol/li[{}]/div/label".format(index)

    attempts = 1
    while True:
        try:
            elem = driver.find_element_by_xpath(salary_button)
            time.sleep(3)
        except Exception as e:
            attempts += 1
            if attempts > 25: 
                break
        else:
            elem.click()
            time.sleep(3)
            driver.find_element_by_xpath(salary_path).click()
            break


def sort_results_by(driver, sorting_criteria):
    """sort results by either relevance or date posted"""

    if sorting_criteria == 'Relevance': return

    button = "button.dropdown-trigger"

    option_path = "html/body/div[3]/div/div[2]/div[1]/div[5]/div[1]/" \
                                "div[2]/form/ul/li[2]/label"

    try:
        time.sleep(3)

        driver.find_element_by_css_selector(button).click()

    except Exception as e:
        print(e)
        print("  Could not sort results by '{}'".format(sorting_criteria))

    else:
        try:
            time.sleep(3)

            driver.find_element_by_xpath(option_path).click()

        except Exception as e:
            print("  Could not select sort by option")
        else:
            time.sleep(3)


def robust_wait_for_clickable_element(driver, delay, selector):
    """ wait for css selector to load """

    clickable = False
    attempts = 1

    try:
        driver.find_element_by_css_selector(selector)

    except Exception as e:
        print("  Selector not found: {}".format(selector))

    else:
        while not clickable:

            try:
                # wait for job post link to load
                wait_for_clickable_element(driver, delay, selector)

            except Exception as e:
                print("  {}".format(e))
                attempts += 1
                if attempts > 10**3: 
                    print("  \nrobust_wait_for_clickable_element failed " \
                                    "after too many attempts\n")
                    break
                pass
            else:
                clickable = True


def robust_click(driver, delay, selector):
    """
    use a while-looop to click an element. For stubborn links.
    """

    try:
        driver.find_element_by_css_selector(selector).click()
    except Exception as e:
        print("  The job post link was likely hidden,\n    An " \
                "error was encountered while attempting to click link" \
                "\n    {}".format(e))

        attempts = 1
        clicked = False

        while not clicked:

            try:
                driver.find_element_by_css_selector(selector).click()
            except Exception as e:
                pass
            else:
                clicked = True
                print("  Successfully navigated to job post page "\
                            "after {} attempts".format(attempts))
            finally:
                attempts += 1
                if attempts > 10**3:
                    print(selector)
                    print("  robust_click method failed after too many attempts")
                    break 


def wait_for_clickable_element(driver, delay, selector):
    """use WebDriverWait to wait for an element to become clickable"""
    
    obj = WebDriverWait(driver, delay).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, selector)
            )
        )

    return obj  


def link_is_present(driver, delay, selector, index, results_page):
    """
    verify that the link selector is present and print the search 
    details to console. This method is particularly useful for catching
    the last link on the last page of search results
    """

    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, selector)
            )
        )

        print("**************************************************")
        print("\nScraping data for result  {}" \
                "  on results page  {} \n".format(index + 1, results_page))

    except Exception as e:
        print(e)
        if index < 24:
            print("\nWas not able to wait for job_selector to load. Search " \
                    "results may have been exhausted.")
            return True
        else:
            return False

    else:
        return True 


def search_suggestion_box_is_present(driver, selector, index, results_page):
    """
    check results page for the search suggestion box,
    as this causes some errors in navigate search results.
    """
    if (index == 0) and (results_page == 1):
        try:
            # This try-except statement allows us to avoid the 
            # problems cause by the LinkedIn search suggestion box
            driver.find_element_by_css_selector("div.suggested-search.bd")
        except Exception as e:
            pass
        else:
            return True
    else:
        return False


def next_results_page(driver, delay):
    """
    navigate to the next page of search results. If an error is encountered
    then the process ends or new search criteria are entered as the current 
    search results may have been exhausted.
    """

    try:
        # wait for the next page button to load
        print("  Moving to the next page of search results... \n" \
                "  If search results are exhausted, will wait {} seconds " \
                "then either execute new search or quit".format(delay))

        wait_for_clickable_element(driver, delay, "li.next a.page-link")

        # navigate to next page
        driver.find_element_by_css_selector("li.next a.page-link").click()

    except Exception as e:
        print ("\nFailed to click next page link; Search results " \
                                "may have been exhausted\n{}".format(e))
        raise ValueError("Next page link not detected; search results exhausted")

    else:
        # wait until the first job post button has loaded
        first_job_button = "li.mod.result.idx1.job div.bd " \
                            "div.srp-actions.blue-button a.primary-action-button.label"

        # wait for the first job post button to load
        wait_for_clickable_element(driver, delay, first_job_button)


def go_to_specific_results_page(driver, delay, page_number):
    """
    go to a specific results page in case of an error, can restart 
    the webdriver where the error occurred.
    """

    if page_number < 2: return

    results_page = 1

    for i in range(page_number):

        results_page += 1
        time.sleep(5)

        try:

            next_results_page(driver, delay)
            print("\n**************************************************")
            print("\n\n\nNavigating to results page {}\n\n\n".format(results_page))

        except ValueError:

            print("**************************************************")
            print("\n\n\n\n\nSearch results exhausted\n\n\n\n\n")


def extract_transform_load(driver, delay, selector, date, job, location, filename):
    """
    using the next job posting selector on a given results page, wait for
    the link to become clickable, then navigate to it. Wait for the job 
    posting page to load, then scrape the page and write the data to file.
    Finally, go back to the search results page
    """

    # wait for the job post to load then navigate to it
    try:
        wait_for_clickable_element(driver, delay, selector)
        
        robust_click(driver, delay, selector)
        
    except Exception as e:
        print("error navigating to job post page")
        print(e)
        pass
            
    try:
        # wait for the premium applicant insights to load
        # wait_for_clickable_element(driver, delay, "div.premium-insights")
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.premium-insights")
                )
            )
    except Exception as e:
        print(e)


    try:
        # scrape page and prepare to write the data to file
        data = scrape_page(driver, keyword=job, location=location, dt=date)
        
    except Exception as e:
        print("\nSearch results may have been exhausted. An error was " \
                "encountered while attempting to scrape page data")
        print(e)

    else:
        # write data to file
        write_line_to_file(filename, data)

    finally:
        if not ("Search | LinkedIn" in driver.title):
            driver.execute_script("window.history.go(-1)")




class LIClient(object):
    def __init__(self, driver, **kwargs):
        self.driver         =  driver
        self.username       =  kwargs["username"]
        self.password       =  kwargs["password"]
        self.filename       =  kwargs["filename"]
        self.date_range     =  kwargs["date_range"]
        self.search_radius  =  kwargs["search_radius"]
        self.sort_by        =  kwargs["sort_by"]
        self.salary_range   =  kwargs["salary_range"]
        self.page_number    =  kwargs["page_number"]


    def driver_quit(self):
        self.driver.quit()


    def login(self):
        """login to linkedin then wait 3 seconds for page to load"""

        # Enter login credentials
        WebDriverWait(self.driver, 120).until(
            EC.element_to_be_clickable(
                (By.ID, "session_key-login")
            )
        )

        elem = self.driver.find_element_by_id("session_key-login")
        elem.send_keys(self.username)
        elem = self.driver.find_element_by_id("session_password-login")
        elem.send_keys(self.password)

        # Enter credentials with Keys.RETURN
        elem.send_keys(Keys.RETURN)

        # Wait a few seconds for the page to load
        time.sleep(3)


    def navigate_to_jobs_page(self):
        """
        navigate to the 'Jobs' page since it is a convenient page to 
        enter a custom job search.
        """
        # Click the Jobs search page
        jobs_link_clickable = False
        attempts = 1

        while not jobs_link_clickable:

            try:
                self.driver.get("https://www.linkedin.com/jobs/?trk=nav_responsive_sub_nav_jobs")

            except Exception as e:
                attempts += 1
                if attempts > 10**3: 
                    print("  jobs page not detected")
                    break
                pass

            else:
                print("**************************************************")
                print ("\n\n\nSuccessfully navigated to jobs search page\n\n\n")
                jobs_link_clickable = True


    def enter_search_keys(self, job='', location=''):
        """
        execute the job search by entering job and location information.
        The location is pre-filled with text, so we must clear it before
        entering our search.
        """
        driver = self.driver

        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located(
                (By.ID, "keyword-search-box")
            )
        )

        # Enter search criteria
        elem = driver.find_element_by_id("keyword-search-box")
        elem.send_keys(job)

        # clear the text in the location box then enter location
        elem = driver.find_element_by_id("location-search-box").clear()
        elem = driver.find_element_by_id("location-search-box")
        elem.send_keys(location)
        elem.send_keys(Keys.RETURN)

        time.sleep(3)
        try:
            num_results = driver.find_element_by_css_selector(
                                                                    "div.search-info p strong").text
        except Exception as e:
            num_results = ''
            pass

        print("**************************************************")
        print("\n\n\n\n\nSearching  {}  results for  '{}'  jobs in  '{}' " \
                "\n\n\n\n\n".format(num_results, job, location))


    def customize_search_results(self, **kwargs):
        """sort results by either relevance or date posted"""

        adjust_date_range(self.driver, kwargs["date_range"])

        adjust_salary_range(self.driver, kwargs["salary_range"])

        adjust_search_radius(self.driver, kwargs["search_radius"])

        # scroll to top of page so the sorting menu is in view
        self.driver.execute_script("window.scrollTo(0, 0);")

        sort_results_by(self.driver, kwargs["sort_by"])

        # scroll to top of page so first result is in view
        self.driver.execute_script("window.scrollTo(0, 0);")


    def navigate_search_results(self, job, location):
        """
        scrape postings for all pages in search results
        """

        driver = self.driver
        search_results_exhausted = False
        page_number = search_keys["page_number"]
        delay = 60

        date = get_date_time()

        # css elements to view job pages
        list_element_tag = "li.mod.result.idx"

        button_tag = ".job div.bd div.srp-actions.blue-button" \
                                 " a.primary-action-button.label"

        # go to a specific results page number if one is specified
        go_to_specific_results_page(driver, delay, page_number)

        results_page = page_number if page_number > 1 else 1


        while not search_results_exhausted:

            for i in range(25):  # 25 results per page

                # define the css selector for the blue 'View' button for job i
                job_selector = list_element_tag + str(i) + button_tag

                if search_suggestion_box_is_present(driver, job_selector, i, results_page):
                    continue

                # wait for the selector for the next job posting to load.
                # if on last results page, then throw exception as job_selector 
                # will not be detected on the page
                if not link_is_present(driver, delay, job_selector, i, results_page):
                    continue

                robust_wait_for_clickable_element(driver, delay, job_selector)
                
                extract_transform_load(driver, delay, job_selector, date, 
                                                                                job, location, self.filename)


            # attempt to navigate to the next page of search results
            # if the link is not present, then the search results have been 
            # exhausted
            try:

                next_results_page(driver, delay)

                print("\n**************************************************")
                print("\n\n\nNavigating to results page  {}\n\n\n".format(results_page + 1))

            except ValueError:

                search_results_exhausted = True

                print("**************************************************")
                print("\n\n\n\n\nSearch results exhausted\n\n\n\n\n")

            else:

                results_page += 1




