import datetime
import threading
import json
import os

import queue
import shutil
from power_meter import PowerMeter

import zipfile

class DBCounter():
    def __init__(self):
        self.value = 0
        self.just_reset=False
    def increment(self,max):
        out_val =self.value
        if self.value>=max:
            self.reset()
            out_val=self.value
        else:
            self.value+=1
            self.just_reset=False
        return out_val
    def reset(self):
        self.value=0
        self.just_reset=True


class UpdateThread(threading.Thread):
    
    def __init__(
            self,
            db,
            fn_list,
            db_counter,
            stopper,
            q,
            pauser,
            *args,
            **kwargs
        ):
        self.args=args
        super().__init__(**kwargs)
        self.db=db.data
        self.db_obj=db
        self.db_lock=db.lock
        self.fn_list=fn_list
        self.db_counter=db_counter
        self.stopper=stopper
        self.q=q
        self.pauser=pauser
    
    # work on updating database and making a manual update feature
    def run(self):
        while True:
            
            with self.db_lock:
                self.i = self.db_counter.increment(len(self.db))
                
            if self.db_counter.just_reset:
                self.db_obj.save_and_bak()

            with self.db_lock:
                db_i = self.db[self.i]
                
            if self.stopper.is_set():
                self.db_obj.save_and_bak()
                break

            for fn in self.fn_list:
                res = fn(db_i,self.db_lock,*self.args)
                if self.pauser.is_set():
                    self.add_to_queue(res)                

            if self.record:
                with self.db_lock:
                    exist = getattr(self,'record_time',False)
                if exist:
                    expired = UpdateThread.record_time<datetime.datetime.now()
                    if expired:
                        self.to_excel()
                        with self.db_lock:
                            UpdateThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))
                else:
                    with self.db_lock:
                        UpdateThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))

            if self.stop_at and UpdateThread.stop_at<datetime.datetime.now() and not self.stopper.is_set():
                self.stopper.set()
                self.db_obj.save_and_bak()
                with self.db_lock:
                    self.db_counter.reset()

            percent_complete = self.i/len(self.db)*100
            print(f'{percent_complete:.2f}%')

    def to_excel(self,no_time=False):
        file = self.db_obj.export()
        log_dir = self.log_dir
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
    def add_to_queue(self,res):
        self.q.put(json.dumps(res))








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

