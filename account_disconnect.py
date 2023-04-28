from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def check_active(driver):
    try:
        error_msg = driver.find_element(By.ID,'error')
        return error_msg.text
    except NoSuchElementException as error:
        return 'acount_active'

def check_restored(driver):
    try:
        msg = driver.find_element(By.ID,'power_outage').text
        date = driver.find_element(By.ID,'outage_report_date').text
        status = f"{msg} {date}"
    except NoSuchElementException as error:  
        status = "device offline"
    return status