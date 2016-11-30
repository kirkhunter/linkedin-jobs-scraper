from __future__ import print_function
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import json
import time


def job_id(driver):
    """
    grabs the meta linkedin unique job id from the url
    e.g. url = https://www.linkedin.com/jobs/view/161251904
    returns 161251904
    """
    elem = driver.find_element_by_xpath("//meta[@property='og:url']")
    url  = elem.get_attribute("content")
    return url[url.find('/', 34) + 1:]

def parse_post_age(text):
        """ map 'posted 10 days ago' => '10' """
        if 'hours' in text:
            return '1'
        return list(filter(lambda c: c.isdigit(), text))

def post_data(driver):
    """
    get post age and page views and trim excess words
    so that 'posted 10 days ago' becomes '10'
    and '63 views' becomes '63' 
    """
    post_info = {
        "post_age"   : "li.posted", 
        "page_views" : "ul.posting-info li.views"
    }
    for key, selector in post_info.items():
        try:
            text = driver.find_element_by_css_selector(selector).text
            if key == "post_age":
                post_info[key] = parse_post_age(text)
            else:
                post_info[key] = list(filter(lambda c: c.isdigit(), text))
        except Exception as e:
            post_info[key] = ""
            pass
    return post_info

def job_data(driver):
    """
    scrapes the posting info for title, company, post age, location,
    and page views. Have seen many strange errors surrounding the
    job tite, company, location data, so have used many try-except
    statements to avoid potential errors with unicode, etc.
    """
    job_info = {
        "job_title"        :  "h1.title",
        "company"          :  "span.company",
        "location"         :  "h3.location",
        "employment_type"  :  "div.employment div.content div.rich-text",
        "industry"         :  "div.industry div.content div.rich-text",
        "experience"       :  "div.experience div.content div.rich-text",
        "job_function"     :  "div.function div.content div.rich-text",
        "description"      :  "div.summary div.content div.description-section div.rich-text"
    }
    # click the 'read more' button to reveal more about the job posting
    try:
        driver.find_element_by_css_selector("button#job-details-reveal").click()
    except Exception as e:
        print("error in attempting to click 'reveal details' button")
        print(e)
    for key, selector in job_info.items():
        try:
            job_info[key] = driver.find_element_by_css_selector(selector).text
        except Exception as e:
            job_info[key] = ""
            pass
    return job_info

def company_data(driver):
    """return company insights, number of employees and average tenure"""
    try:
        stats_selector = "ul.company-growth-stats.stats-list li"
        company_stats  = driver.find_elements_by_css_selector(stats_selector)
        company_info   = [stat.text for stat in company_stats]
    except Exception as e:
        print("error acquiring company info")
        print(e)
    else:
        try:
            employees     = list(filter(lambda text: 'employees' in text, company_info))
            num_employees = list(filter(lambda c: c.isdigit(), employees[0]))
        except Exception as e:
            num_employees = ""
            pass
        try:
            tenure        = list(filter(lambda text: 'tenure' in text, company_info))
            avg_tenure    = list(filter(lambda c: c in '0123456789.', tenure[0]))
        except Exception as e:
            avg_tenure    = ""
            pass
        company_info  = {
            "avg_tenure"    : avg_tenure, 
            "num_employees" : num_employees
        }
    return {"avg_tenure" : avg_tenure, "num_employees" : num_employees}

def salary_data(driver):
    """
    scrapes the salary info chart on the right panel returns lower, 
    upper bounds on salary estimate as well as average salary
    """
    try:
        _base = driver.find_element_by_xpath('/descendant::p[@class="salary-data-amount"][1]').text
        _total = driver.find_element_by_xpath('/descendant::p[@class="salary-data-amount"][2]').text
        return {
            "min" : list(filter(lambda c: c.isdigit(), _base)),
            "max" : list(filter(lambda c: c.isdigit(), _total))
        }
    except Exception as e:
        print("error acquiring salary info")
        print(e)
        pass
    return {"min": "", "max": "", "avg": ""}


def num_applicants(driver):
    """
    Grabs number of applicants from either the header of the 
    applicants-insights div, or within the applicants-table in the same 
    div element. Returns empty string if data is not available.
    """
    # use two selectors since LI has two methods of showing number
    # of applicants in the applicants-insights driver
    num_applicant_selectors = [
        "span.applicant-rank-header-text",
        "table.other-applicants-table.comparison-table tr td",
        "p.number-of-applicants"
    ]
    for selector in num_applicant_selectors:
        try:
            num_applicants = driver.find_element_by_css_selector(selector).text
        except Exception as e:
            pass
        else:
            return list(filter(lambda c: c.isdigit(), num_applicants))
    return ''

def applicants_education(driver):
    """return dictionary of applicant education levels"""
    education_selector = "table.applicants-education-table.comparison-table tbody tr"
    try:
        education = driver.find_elements_by_css_selector(education_selector)
        if education:
            # grab the degree type and proportion of applicants with that
            # degree.
            remove = ["have", "a", "Degree", "degrees", "(Similar", "to", "you)"]
            edu_map = list(map(
                    lambda edu: list(filter(
                            lambda word: word not in remove, 
                            edu
                        )), 
                    [item.text.split() for item in education]
                ))
            # store the education levels in a dictionary and prepare to 
            # write it to file
            edu_dict = {
                "education" + str(i + 1) : { 
                                    "degree" : ' '.join(edu_map[i][1:]), 
                                    "proportion": edu_map[i][0]
                                } 
                for i in range(len(edu_map))
            }
            return edu_dict
    except Exception as e:
        print("error acquiring applicants education")
        print(e)
    return {}

def applicants_locations(driver):
    """
    scrapes the applicants-insights-hover-content div on a 
    given job page. Grabs the location and number of applicants 
    from each location.
    """
    applicants_info = {}
    try:
        elem = driver.find_elements_by_css_selector("a.location-title")
        for i in range(len(elem)):
            # city and applicants are separated by a new line
            city, applicants = elem[i].text.split('\n')
            # get number of applicants by removing the word 'applicants'
            applicants = applicants[:applicants.find(" applicants")]
            # enter, typically, three applicant location data pairs
            location_data  = {
                "city"       : city, 
                "applicants" : applicants
            }
            applicants_info["location" + str(i + 1)] = location_data
    except Exception as e:
        print("error acquiring applicants locations")
        print(e)
    return applicants_info

def applicants_skills(driver):
    """
    scrapes applicant skills by finding 'pill' tags in html
    returns list of skills. If skills not present on page, then
    returns empty list
    """
    try:
        raw_skills = driver.find_elements_by_css_selector("span.pill")
        skills     = [skill.text for skill in raw_skills] 
        return skills
    except Exception as e:
        print("error acquiring applicant skills")
        print(e)
    return []

def scrape_page(driver, **kwargs):
    """
    scrapes single job page after the driver loads a new job posting.
    Returns data as a dictionary
    """
    # wait ~1 second for elements to be dynamically rendered
    time.sleep(1.2)
    start = time.time()
    containers = [
        "section#top-card div.content",            # job content
        "div.job-salary-container",                # job salary
        "ul.company-growth-stats.stats-list",      # company stats
        "div.insights-card.applicants-skills",     # applicants skills
        "div.applicants-locations-list"            # applicants locations
    ]
    for container in containers:
        try:
            WebDriverWait(driver, .25).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, container)
                    )
                )
        except Exception as e:
            print("timeout error waiting for container to load or element" \
                  " not found: {}".format(container))
            print(e)
    applicant_info = {
        "num_applicants"    :  num_applicants(driver),
        "skills"            :  applicants_skills(driver),
        "education"         :  applicants_education(driver),
        "locations"         :  applicants_locations(driver)
    }
    job_info = {
        "job_id"            :  job_id(driver),
        "salary_estimates"  :  salary_data(driver),
        "company_info"      :  company_data(driver)
    }
    job_info.update(job_data(driver))
    data = {
        "applicant_info"    :  applicant_info,
        "job_info"          :  job_info,
        "post_info"         :  post_data(driver),
        "search_info"       :  kwargs
    }
    print("scraped page in  {}  seconds\n".format(time.time()-start))
    # try:
    #     print("data:\n\n{}\n".format(data))
    # except Exception as e:
    #     print("data could not be printed to console\n")
    return data
