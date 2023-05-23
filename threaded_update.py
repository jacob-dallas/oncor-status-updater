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
import concurrent.futures
import threading
import json
from power_meter import PowerMeter

thread_local = threading.local()
lock = threading.Lock()



def get_driver():
    if not hasattr(thread_local,'driver'):
        thread_local.driver = webdriver.Chrome(service=service, options=options)
    return thread_local.driver

def updates(meter):
        global last_complete_entry
        global meters
        # Keeps a live updated on percentage complete

        obj = PowerMeter(meter)
        # Safely writes to outage log
        with lock:
            outage_log.write(
                f'{datetime.datetime.now()}: ESI ID \"{obj.id}\": beginning search\n'
            )

        # Begins the search web interface
        driver = get_driver()
        status,log_str = obj.get_status(driver)
        obj.online_status=status

        with lock:
            percent_complete = last_complete_entry/n_meters*100
            last_complete_entry += 1
            print(f'{percent_complete:.2f}%')
            outage_log.write(log_str)
            i = sig_meters.index(meter)
            meters['Traffic Signals'][i] = obj.__dict__ 

def quit_driver(thread):
    if hasattr(thread_local,'driver'):
        thread_local.driver.quit()
        delattr(thread_local,'driver')

def parallel_update(ids):
    n_threads = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        try:
            executor.map(updates,ids)
        finally:
            executor.map(quit_driver,range(n_threads))

def full_scan():
    start_time = datetime.datetime.now()
    service = Service(executable_path="chromedriver113.exe")
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless=new')
    options.accept_insecure_certs=True
    with open('power.json','r') as f:
        meters = json.load(f)

    sig_meters = meters['Traffic Signals']

    outage_log = open('outage_log.txt','w')

    # Keep track of progress
    last_complete_entry = 0
    n_meters = len(sig_meters)

    # Multi-Thread the search process
    parallel_update(sig_meters)

    # Time the process
    finish_time = datetime.datetime.now()
    delta = finish_time-start_time
    outage_log.write(f'updating {last_complete_entry} meters took {delta.seconds} seconds')

    # Close the log
    outage_log.close()

    # Write the search results
    with open('update.json','w') as f:
        json.dump(meters,f,indent=1)
    # outages.to_excel(f'logs\excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.xlsx','sheet1',index=False)

    # TODO: http connection pool error and can threads access non-threaded scope?
    # Everything writes to the log correctly, but the pool error stops it from 
    # geting info
    
if __name__ == '__main__':
    full_scan()