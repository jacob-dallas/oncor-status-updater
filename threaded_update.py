import datetime
from os import path
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import concurrent.futures
import threading
import json
from power_meter import PowerMeter
import message
from webdriver_manager.chrome import ChromeDriverManager
from pythonping import ping
from controller_snmp import controller_ping

thread_local = threading.local()
lock = threading.Lock()

async def continuous_update(broadcast):
    while True:
        full_scan(broadcast)

def get_driver():
    if not hasattr(thread_local,'driver'):
        thread_local.driver = webdriver.Chrome(service=service, options=options)
    return thread_local.driver

def updates(meter):
    global last_complete_entry
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
    n_threads = 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        try:
            executor.map(updates,ids)
        finally:
            executor.map(quit_driver,range(n_threads))

def full_scan(broadcast = False):
    global service
    global options
    global n_meters
    global last_complete_entry
    global meters
    global outage_log
    global sig_meters
    start_time = datetime.datetime.now()
    service = Service()
    options = Options()
    options.accept_insecure_certs = True
    options.add_argument('--headless=new')
    # with open('power.json','r') as f:
    #     meters = json.load(f)

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

    # Write the search resultsoperate threads over list without executor python
    # with open('update.json','w') as f:
    #     json.dump(meters,f,indent=1)
    # outages.to_excel(f'logs\excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.xlsx','sheet1',index=False)

# need to create a function where meter doesn't need to be passed so i can run 
# parallel without executor so threads can run along side main thread.
def update_noexec(queue):
    global last_complete_entry
    global n_meters

    while True:
        try:
            with lock:
                thread_local.i = last_complete_entry
                if thread_local.i > n_meters:
                    last_complete_entry = 0
                else:
                    last_complete_entry += 1
                thread_local.i = last_complete_entry
        finally:
            quit_driver(1)
        
        meter = sig_meters[thread_local.i]
        updates(meter)

class UpdateThread(threading.Thread):
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.accept_insecure_certs = True
    options.add_argument('--headless=new')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")


    
    lock = threading.Lock()
    last_complete_entry = 0
    
    def __init__(self, queue,**kwargs):
        super().__init__(**kwargs)
        self.queue = queue
    
    def run(self):
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        try:
            while True:
                with self.lock:
                    self.i = UpdateThread.last_complete_entry
                    if self.i > UpdateThread.n_meters:
                        UpdateThread.last_complete_entry = 0
                        self.i = UpdateThread.last_complete_entry
                        # add a function in here to search for a specific meter
                    else:
                        UpdateThread.last_complete_entry += 1
            
                meter = UpdateThread.sig_meters[self.i]
                self.update(meter)
        finally:
            self.driver.quit()
    
    def update(self,meter):

        obj = PowerMeter(meter)

        # Safely writes to outage log
        with lock:
            UpdateThread.outage_log.write(
                f'{datetime.datetime.now()}: ESI ID \"{obj.id}\": beginning search\n'
            )

        # Begins the search web interface
        status,log_str = obj.get_status(self.driver)
        obj.online_status=status

        with self.lock:
            percent_complete = self.i/self.n_meters*100
            self.last_complete_entry += 1
            print(f'{percent_complete:.2f}%')
            self.outage_log.write(log_str)
            UpdateThread.meters['Traffic Signals'][self.i] = obj.__dict__ 
            self.queue.put(json.dumps(obj.__dict__))


class CommThread(threading.Thread):
    status_dict = {
        "160":"Cabinet Flash",
        "32":"Cabinet Flash",
        "48":"Local Flash",
        "128":"Coordination",
         
    }
    def __init__(self,queue,**kwargs):
        super.__init__(**kwargs)
        self.queue = queue
    def run(self, signals):
        for signal in signals:
            modem_online = ping(signal['ip'],count=1).success()
            controller_online = controller_ping(signal['ip'])
            if controller_online:
                status_code = controller_online.variableBindngs.variables.__getitem__(0).value.value
                controller_status = self.status_dict.get(str(status_code),'Free/Unregistered Status')
                controller_online = True
            else:
                controller_status = "N/A"
            self.queue.put(json.dumps({
                "modem_online":modem_online,
                "controller_online":controller_online,
                "controller_status":controller_status
            }))

if __name__ == '__main__':
    ma = message.MessageAnnouncer()
    thread_1 = UpdateThread(ma,name='thread_1')
    thread_2 = UpdateThread(ma,name='thread_2')
    thread_1.start()
    thread_2.start()
