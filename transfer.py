import pandas as pd
import datetime
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time 
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
from account_disconnect import check_active, check_restored

def next(driver):

    next_button = driver.find_element(value='next')
    next_button.click()
    return True

def grab_status(driver):
    status = driver.find_element(value='label_no_omscall_fault')
    return status.text



def full_scan():
    startnumber = 0

    start_time = datetime.datetime.now()
    load_time = 0.1
    service = Service(executable_path="chromedriver.exe")
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.accept_insecure_certs=True
    driver = webdriver.Chrome(service=service, options=options)
    outages = pd.read_excel('Traffic Signal Spreadsheets.xlsx','ONCOR', converters={"ESI ID": str})
    outage_log = open('outage_log.txt','w')
    last_complete_entry = 0
    try:
        for i,id in enumerate(outages['ESI ID']):
            if i < startnumber:
                continue
            percent_complete = i/outages['ESI ID'].size*100
            print(f'{percent_complete:.2f}%')
            outage_log.write(f'{datetime.datetime.now()}: ESI ID \"{id}\": beginning search\n')
            try:

                driver.get("https://www.oncor.com/outages/check_status/identify/esi")


                id_input = driver.find_element(value='esi_id_text')
                next_button = driver.find_element(value='next')
                id_input.clear()
                id_input.send_keys(id)
                next_button.click()


                WebDriverWait(
                    driver, 
                    5,
                    ignored_exceptions=[StaleElementReferenceException]
                ).until(next)


                try:
                    status = WebDriverWait(
                        driver, 
                        5,
                        ignored_exceptions=[StaleElementReferenceException]
                    ).until(
                        grab_status
                    )
            
                    print('here')


                except (NoSuchElementException, TimeoutException) as error:
                    status = check_restored(driver)

                outages['Status'][i] = status
                outage_log.write(f'{datetime.datetime.now()}: ESI ID \"{id}\" status: {status}\n')
            except StaleElementReferenceException as error:
                outage_log.write(f'{datetime.datetime.now()}: ESI ID \"{id}\": [ERROR] search was too fast, status was not updated\n')
                print(f'{datetime.datetime.now()}: ESI ID \"{id}\": [ERROR] search was too fast, status was not updated\n')
            except ElementClickInterceptedException as error:
                msg = check_active(driver)
                if msg == 'acount_active':
                    raise Exception
                outage_log.write(f'{datetime.datetime.now()}: [ERROR] {msg}\n')
                outages['Status'][i] = msg
            last_complete_entry = i
    except Exception as error:
        print("an error occured\n")
        print(error)
        outage_log.write(f'{datetime.datetime.now()}: [ERROR] a fatal error occured\n')
    finally:

        finish_time = datetime.datetime.now()
        delta = finish_time-start_time
        outage_log.write(f'updating {last_complete_entry} meters took {delta.seconds} seconds')
        outages.to_excel(f'logs\excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.xlsx','sheet1',index=False)
        outage_log.close()
        driver.quit()


    print(delta)

if __name__ == '__main__':
    full_scan()