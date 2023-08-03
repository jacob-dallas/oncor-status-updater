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

class DBCounter():
    def __init__(self):
        self.value = 0
        self.just_reset=False
    def increment(self,max):
        if self.value>max:
            self.reset()
        else:
            self.value+=1
        return self.value
    def reset(self):
        self.value=0
        self.just_reset=True
        

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
    
    def __init__(
            self,
            db,
            db_lock,
            fn_list,
            db_counter,
            stopper,
            queue,
            pauser,
            **kwargs
        ):
        super().__init__(**kwargs)
        self.db=db
        self.db_lock=db_lock
        self.fn_list=fn_list
        self.db_counter=db_counter
        self.stopper=stopper
        self.q=queue
        self.pauser=pauser
    
    # work on updating database and making a manual update feature
    def run(self):
        while True:
            
            with self.db_lock:
                self.i = self.db_counter.increment(len(self.db))
                if self.db_counter.just_reset:
                    self.stopper.set()
                db_i = UpdateThread.db[self.i]
                if self.stopper.is_set():
                    break

            for fn in self.fn_list:

                res = fn(db_i,self.db_lock)
                if not self.pauser.is_set():
                    self.add_to_queue(res)

            if self.i%100==0:
                with self.db_lock:
                    self.save_and_bak()

            if self.record:
                with self.db_lock:
                    exist = getattr(self,'record_time',False)
                    if exist:
                        expired = UpdateThread.record_time<datetime.datetime.now()
                        if expired:
                            self.to_excel()
                            UpdateThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))
                    else:
                        UpdateThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))

            if self.stop_at and UpdateThread.stop_at<datetime.datetime.now() and not self.stopper.is_set():
                print('stopping now!')
                with self.db_lock:
                    self.stopper.set()
                    self.db_counter.reset()
                    self.save_and_bak()

            percent_complete = self.i/len(self.db)*100
            print(f'{percent_complete:.2f}%')
            
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

