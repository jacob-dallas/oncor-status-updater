import datetime
import threading
import json
import os
from pythonping import ping
from controller_snmp import controller_ping
import queue
import shutil

from power_meter import PowerMeter

# outages.to_excel(f'logs\excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.xlsx','sheet1',index=False)

class UpdateThread(threading.Thread):

    status_dict = {
        "160":"Cabinet Flash",
        "32":"Cabinet Flash",
        "48":"Local Flash",
        "128":"Coordination",  
    }

    res_dict = {
        'ON':'&#9889',
        'INACTIVE': 'inactive',
        'TEMP_DISCONNECT': 'inactive',
        'no_id': 'inactive',
        'bad_id': 'inactive',
        'unknown': 'unknown'
    }

    lock = threading.Lock()
    last_complete_entry = 0
    stop = False
    
    def __init__(self, queue,**kwargs):
        super().__init__(**kwargs)
        self.queue = queue

    
    @property
    def n_signals(self) -> int:
        return len(self.signals)
    
    def set_stop(self,value = False):
        self.stop = value
    
    # work on updating database and making a manual update feature
    def run(self):
        while True:
            if self.stop:
                break
            with self.lock:
                self.i = UpdateThread.last_complete_entry
                if self.i > self.n_signals-1:
                    UpdateThread.last_complete_entry = 0
                    self.i = UpdateThread.last_complete_entry
                    # add a function in here to search for a specific meter
                else:
                    UpdateThread.last_complete_entry += 1

            signal = UpdateThread.signals[self.i]

            res = oncor(signal,self.lock,self.outage_log)
            self.add_to_queue(res)
            
            res = controller(signal,self.lock,self.outage_log)
            self.add_to_queue(res)

            res = time_res(signal,self.lock,self.outage_log)
            self.add_to_queue(res)

            if self.i%100==0:
                self.save_and_bak()

            with self.lock:
                percent_complete = self.i/self.n_meters*100
                self.last_complete_entry += 1
                print(f'{percent_complete:.2f}%')
    
    
    def add_to_queue(self,res):
        self.queue.put(json.dumps(res))

    def save_and_bak(self):
        with self.lock:
            shutil.copy(self.db,os.path.join(self.data_root,'signals.bak'))
            with open(self.db,'w') as f:
                json.dump(self.signals,f)
            


def oncor(signal,lock,log):
    preffered_ind = 0
    if len(signal['meters'])>1:
        for i,meter in enumerate(signal['meters']):
            if ('new' in meter['comment'].lower()):
                preffered_ind = i
    if len(signal['meters'])==0:
        print('no_meter')
        res = {
            'cog_id':signal['cog_id'],
            'online_status': 'no_meter',
            'id': 'N/A'
        }
    else:
        meter = signal['meters'][preffered_ind]

        obj = PowerMeter(meter)

        # Safely writes to outage log
        with lock:
            log.write(
                f'{datetime.datetime.now()}: ESI ID \"{obj.id}\": beginning search\n'
            )

        # Begins the search web interface
        status = obj.http_get()

        obj.online_status = status

        with lock:
            signal['meters'][preffered_ind] = obj.__dict__
            log.write(status)

        res = obj.__dict__
    return res

def controller(signal,lock,log):
    if signal['ip'] == '0.0.0.0':
        controller_online = 'unknown/noip'
        modem_online = 'unknown/noip'
        controller_status = 'unknown/noip'
    else:
        ip = signal['ip'].split(':')[0]
        modem_online = ping(ip,count=1).success()
        controller_online = controller_ping(ip)
        if controller_online:
            status_code = controller_online.variableBindings.variables.__getitem__(0).value.value
            controller_status = UpdateThread.status_dict.get(str(status_code),'Free/Unregistered Status')
            controller_online = True
        else:
            controller_status = "N/A"
    res = {
        "cog_id":signal["cog_id"],
        "modem_online":modem_online,
        "controller_online":controller_online,
        "controller_status":controller_status
    }
    with lock:
        signal["modem_online"] = modem_online
        signal["controller_online"] = controller_online
        signal["controller_status"] = controller_status
        log.write(f'modem_online: {modem_online}')
    return res

def time_res(signal,lock,log):
    updated_at = str(datetime.datetime.now())
    res = {
        "cog_id":signal["cog_id"],
        'time':updated_at
    }
    with lock:
        signal["updated_at"] = updated_at
        log.write(f'signal {signal["cog_id"]} was updated at {updated_at}')
    return res

if __name__ == '__main__':
    with open('power.json','r') as f:
        signals = json.load(f)

        
    outage_log = open('outage_log.txt','w')
    UpdateThread.signals = signals
    UpdateThread.outage_log = outage_log
    
    UpdateThread.n_meters = len(UpdateThread.signals)
    ma = queue.Queue(10)
    thread_1 = UpdateThread(ma,name='thread_1')
    thread_2 = UpdateThread(ma,name='thread_2')
    thread_1.start()
    thread_2.start()
