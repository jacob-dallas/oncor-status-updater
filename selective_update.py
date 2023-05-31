import json
import datetime
import pandas as pd
import zipfile
import os
from cut import devices
import power_meter as pm
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def scan():

    with open('power_cut.json','r') as f:
        data = json.load(f)
    service = Service(executable_path="chromedriver.exe")
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless=new')
    options.accept_insecure_certs=True
    driver = webdriver.Chrome(service=service, options=options)

    key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiJhYjM0YTUwMS0zMDJjLTQ5NzItYThlMi1lYmUxNDMzNGY5ZTAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8yOTM1NzA5ZS1jMTBjLTQ4MDktYTMwMi04NTJkMzY5Zjg3MDAvIiwiaWF0IjoxNjg1MTA0NjY2LCJuYmYiOjE2ODUxMDQ2NjYsImV4cCI6MTY4NTEwOTIzMiwiYWNyIjoiMSIsImFpbyI6IkFUUUF5LzhUQUFBQTdUUXlGU1QvdlVXbHdDZTd4ZTBrcEc2Qm5DbHdHRGFMV0Vpb1Mwam1GNGxHK3BYMVU1bEtHaUt5bTh0dTlrQW8iLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiYWIzNGE1MDEtMzAyYy00OTcyLWE4ZTItZWJlMTQzMzRmOWUwIiwiYXBwaWRhY3IiOiIxIiwiZmFtaWx5X25hbWUiOiJQYXZlbGthIiwiZ2l2ZW5fbmFtZSI6IkphY29iIiwiaXBhZGRyIjoiNjYuOTcuMTQ1LjY1IiwibmFtZSI6IlBhdmVsa2EsIEphY29iIiwib2lkIjoiNTE5ZWE1NmUtZWFkOC00ZTVkLTkyY2EtOWEyOGFlNzAyMTJjIiwib25wcmVtX3NpZCI6IlMtMS01LTIxLTEwODUwMzEyMTQtMTY3NzEyODQ4My03MjUzNDU1NDMtMjEwNDcxIiwicmgiOiIwLkFUY0FubkExS1F6QkNVaWpBb1V0TnAtSEFBR2xOS3NzTUhKSnFPTHI0VU0wLWVBM0FPay4iLCJzY3AiOiJVc2VyLlJlYWQiLCJzdWIiOiJ5cHVsa09PVEt3OGZXX0twbUZfVUVEQkliRmgyN2tieHNZTlZPVUFSTEpRIiwidGlkIjoiMjkzNTcwOWUtYzEwYy00ODA5LWEzMDItODUyZDM2OWY4NzAwIiwidW5pcXVlX25hbWUiOiJqYWNvYi5wYXZlbGthQGRhbGxhc2NpdHloYWxsLmNvbSIsInVwbiI6ImphY29iLnBhdmVsa2FAZGFsbGFzY2l0eWhhbGwuY29tIiwidXRpIjoiaVNRRkhsdFVBMEtNV2ZWUDVGRGZBQSIsInZlciI6IjEuMCJ9.hS-5jRskL4js4DIukIYW7cM1f-_zMTu8wmmZwhSmZ6mQnSdnVr7L2FytaxxOquypI03H5hvNc8S9LxiNzU2_2MGVVaaJ1T7GclRni-hQelsrXm3s96dWCqskAjaeNGnwRRZMxslpmqqB7FhHmYjVD5uAg0M_8Wh2tC3IuuKd5IVTep9cMfvBA9rYLr4h4xE3JXzrm6uU8Cc77y1Y9fUNs5pha6keLxBI9-dSb7CjZBHBMMRIfMumZ7PE59wm6vgEMp2FYT-C0yNjQUs2GcRzULpSgDkAovwoHYg_zImoF-ng22mIpYHqv8wJRQr3EoBJRHIZx5dyznnqoRUem64Lsw'
    try:
        while True:
            res = devices(key)

            cut_data = json.loads(res.text)['devices']
            out_data = []
            for device in cut_data:
                try:
                    if device['status']['code']==40 and device['interApplicationId']:
                        meter = next((item for item in data if item["cog_id"] == int(device['interApplicationId'])), None)
                        obj = pm.PowerMeter(meter)
                        status, log_str = obj.get_status(driver)
                        obj.online_status=status
                        out_data.append(obj.__dict__)

                except (KeyError, TypeError):
                        continue
                except Exception as error:
                    print("an error occured\n")
                    print(error)
                    status = 'An unknown error occured; status update cannot be guaranteed'
                    obj.online_status=status
            finish_time = datetime.datetime.now()
            df = pd.DataFrame(out_data)
            df.to_excel(f'logs\excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.xlsx','sheet1',index=False)
            #zip files
            xl_files = []
            files = os.listdir('./logs')
            for f in files:
                if (f.endswith('.xlsx')):
                    xl_files.append(f)
            
            if len(xl_files)>9:
                with zipfile.ZipFile(f'logs\excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.zip', mode='w') as archive:
                    for f in xl_files:
                        archive.write(os.path.join('logs',f))
                        os.remove(os.path.join('logs',f))
    finally:
        driver.quit()

if __name__=='__main__':
    scan()
    