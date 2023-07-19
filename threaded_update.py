import datetime
import threading
import json
import os
from pythonping import ping
from controller_snmp import controller_ping
import queue
import shutil
from json_to_excel import export_sig
from power_meter import PowerMeter

import zipfile

def n_power_updaters():
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, UpdateThread):
            i+=1
    return i
def stop_power():
    for thread in threading.enumerate():
        if isinstance(thread, UpdateThread):
            thread.set_stop(True)
    

# add update schedule

class UpdateThread(threading.Thread):
    one_run=False
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
            
            with self.lock:
                self.i = UpdateThread.last_complete_entry
                if self.i > self.n_signals-1:
                    if self.one_run:
                        stop_power()
                    UpdateThread.last_complete_entry = 0
                    self.i = UpdateThread.last_complete_entry
                    # add a function in here to search for a specific meter
                else:
                    UpdateThread.last_complete_entry += 1
            if self.stop:
                break

            signal = UpdateThread.signals[self.i]

            res = oncor(signal,self.lock,self.outage_log)
            if not self.pause:
                self.add_to_queue(res)
            
            res = controller(signal,self.lock,self.outage_log)
            if not self.pause:
                self.add_to_queue(res)

            res = time_res(signal,self.lock,self.outage_log)
            if not self.pause:
                self.add_to_queue(res)

            if self.i%100==0:
                self.save_and_bak()

            if self.record:
                with self.lock:
                    exist = getattr(self,'record_time',False)
                    if exist:
                        expired = UpdateThread.record_time<datetime.datetime.now()
                        if expired:
                            self.to_excel()
                            UpdateThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))
                    else:
                        UpdateThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))

            if self.stop_at and UpdateThread.stop_at<datetime.datetime.now() and not self.stop:
                print('stopping now!')
                with UpdateThread.lock:
                    stop_power()
                    UpdateThread.last_complete_entry = 0
                self.save_and_bak()


            with self.lock:
                percent_complete = self.i/self.n_signals*100
                self.last_complete_entry += 1
                print(f'{percent_complete:.2f}%')
    
    
    def add_to_queue(self,res):
        self.queue.put(json.dumps(res))

    def save_and_bak(self):
        with self.lock:
            shutil.copy(self.db,os.path.join(self.data_root,'signals.bak'))
            with open(self.db,'w') as f:
                json.dump(self.signals,f)

    def to_excel(self,no_time=False):
        file = export_sig(UpdateThread.signals)
        log_dir = os.path.join(UpdateThread.data_root,'logs')
        finish_time = datetime.datetime.now()
        if no_time:
            filename = 'excel_out.xlsx'
        else:
            filename = f'excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.xlsx'

        outpath = os.path.join(log_dir,filename)
        with open(outpath,'wb') as f:
            f.write(file.getbuffer())
        xl_files = []
        files = os.listdir(log_dir)
        for f in files:
            if (f.endswith('.xlsx')):
                xl_files.append(f)
        
        if len(xl_files)>9:
            filename = f'excel_out_{finish_time.month}-{finish_time.day}_{finish_time.hour}.{finish_time.minute}.zip'
            outpath = os.path.join(log_dir,filename)
            with zipfile.ZipFile(outpath, mode='w') as archive:
                for f in xl_files:
                    archive.write(os.path.join(log_dir,f))
                    os.remove(os.path.join(log_dir,f))

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
        obj.cog_id = signal['cog_id']

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
    UpdateThread.db = 'data/test.json'
    with open(UpdateThread.db,'r') as f:
        signals = json.load(f)

    if not os.path.isdir('data/logs'):
        os.mkdir('data/logs')
    outage_log = open('data/outage_log.txt','w')
    UpdateThread.signals = signals
    UpdateThread.one_run = True
    UpdateThread.outage_log = outage_log
    UpdateThread.pause = True
    UpdateThread.record = False
    UpdateThread.stop_at = False
    UpdateThread.data_root = 'data/'
    UpdateThread.n_signals = len(UpdateThread.signals)
    ma = queue.Queue(10)

    threads = []
    for thread in range(10):
        thread_i = UpdateThread(ma)
        threads.append(thread_i)
        thread_i.start()

    for thread in threads:
        thread.join()

    threads[0].to_excel(no_time=True)

