import pandas as pd
import datetime
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time 
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

start_time = datetime.datetime.now()
load_time = 1
service = Service(executable_path="chromedriver.exe")
options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.accept_insecure_certs=True
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(1)
outages = pd.read_excel('Traffic Signal Spreadsheets.xlsx','ONCOR', converters={"ESI ID": str})
outage_log = open('outage_log.txt','w')
last_complete_entry = 0
try:
    for i,id in enumerate(outages['ESI ID']):
        percent_complete = i/outages['ESI ID'].size
        print(f'{percent_complete:.2f}%')
        outage_log.write(f'{datetime.datetime.now()}: ESI ID \"{id}\": beginning search\n')
        try:
            driver.get("https://www.oncor.com/outages/check_status/identify/esi")
            id_input = driver.find_element(value='esi_id_text')
            next_button = driver.find_element(value='next')
            id_input.send_keys(id)
            next_button.click()
            #add check to see if account is "unregistered"
            ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)
            time.sleep(load_time)
            next_button = WebDriverWait(
                driver, 
                5,
                ignored_exceptions=ignored_exceptions
            ).until(
                expected_conditions.presence_of_element_located((By.ID, 'next'))
            )
            next_button.click()
            try:
                time.sleep(load_time)
                status = WebDriverWait(
                    driver, 
                    5,
                    ignored_exceptions=ignored_exceptions
                ).until(
                    expected_conditions.presence_of_element_located((By.ID, 'label_no_omscall_fault'))
                )  
        
                status = status.text
            except NoSuchElementException as error:
                status = 'power failure'

            outages['Status'][i] = status
            outage_log.write(f'{datetime.datetime.now()}: ESI ID \"{id}\" status: {status}\n')
        except StaleElementReferenceException as error:
            outage_log.write(f'{datetime.datetime.now()}: ESI ID \"{id}\": [ERROR] search was too fast, status was not updated\n')
        last_complete_entry = i
except:
    print("an error occured")
    outage_log.write(f'{datetime.datetime.now()}: a fatal error occured')
finally:

    finish_time = datetime.datetime.now()
    delta = finish_time-start_time
    outage_log.write(f'updating {last_complete_entry} meters took {delta.seconds} seconds')
    outages.to_excel('excel_out.xlsx','sheet1',index=False)
    outage_log.close()
    driver.quit()


print(delta)