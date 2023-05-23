import power_meter as pm
import json
import datetime
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

with open('power.json','r') as f:
    meters = json.load(f)

start_time = datetime.datetime.now()
service = Service(executable_path="chromedriver.exe")
options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--headless=new')
options.accept_insecure_certs=True
driver = webdriver.Chrome(service=service, options=options)
size = len(meters['Traffic Signals'])
outage_log = open('outage_log.txt','w')

for i,meter in enumerate(meters['Traffic Signals']):
    percent_complete = i/size*100
    print(f'{percent_complete:.2f}%')

    
    obj = pm.PowerMeter(meter)
    outage_log.write(
        f'{datetime.datetime.now()}: ESI ID \"{obj.id}\": beginning search\n'
    )
    status, log_str = obj.get_status(driver)
    obj.online_status=status
    outage_log.write(log_str)
    meters['Traffic Signals'][i] = obj.__dict__

finish_time = datetime.datetime.now()
delta = finish_time-start_time
outage_log.write(f'updating {size} meters took {delta.seconds} seconds')

driver.quit()
outage_log.close()

with open('update.json','w') as f:
    json.dump(meters,f,indent=1)