import requests
import snmp
import re
import json
import threading
from threaded_update import time_res, controller
import copy
import os
import shutil
import datetime
import queue


def n_radar_updaters():
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, RadarThread):
            i+=1
    return i
def stop_radar():
    for thread in threading.enumerate():
        if isinstance(thread, RadarThread):
            thread.set_stop(True)
    

# add update schedule

class RadarThread(threading.Thread):
    one_run=False

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
                self.i = RadarThread.last_complete_entry
                if self.i > self.n_signals-1:
                    if self.one_run:
                        stop_radar()
                    RadarThread.last_complete_entry = 0
                    self.i = RadarThread.last_complete_entry
                    # add a function in here to search for a specific meter
                else:
                    RadarThread.last_complete_entry += 1
                signal = RadarThread.signals[self.i]
            if self.stop:
                break

            

            get_devices(signal,self.lock,self.log)

            res = radar_check(signal,self.lock,self.log)
            if not self.pause:
                self.add_to_queue(res)

            res = controller(signal,self.lock,self.log)
            if not self.pause:
                self.add_to_queue(res)

            res = time_res(signal,self.lock,self.log)
            if not self.pause:
                self.add_to_queue(res)

            if self.i%100==0:
                self.save_and_bak()

            if self.record:
                with self.lock:
                    exist = getattr(self,'record_time',False)
                    if exist:
                        expired = RadarThread.record_time<datetime.datetime.now()
                        if expired:
                            self.to_excel()
                            RadarThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))
                    else:
                        RadarThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))

            if self.stop_at and RadarThread.stop_at<datetime.datetime.now() and not self.stop:
                print('stopping now!')
                with RadarThread.lock:
                    stop_radar()
                    RadarThread.last_complete_entry = 0
                self.save_and_bak()


            with self.lock:
                percent_complete = self.i/self.n_signals*100
                print(f'{percent_complete:.2f}%')
    
    
    def add_to_queue(self,res):
        self.queue.put(json.dumps(res))

    def save_and_bak(self):
        with self.lock:
            shutil.copy(self.db,os.path.join(self.data_root,'signals.bak'))
            with open(self.db,'w') as f:
                json.dump(self.signals,f,indent=4)

    def to_excel(self,no_time=False):
        file = export_sig(RadarThread.signals)
        log_dir = os.path.join(RadarThread.data_root,'logs')
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



def get_devices(signal,lock,log):

    with lock:
        ip = signal['ip']

    ip = signal['ip'].split(':')[0]
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        res = requests.post(url,data=data,timeout=2)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        url = f"http://{ip}:8080/api/config/firewall/portfwd/"

        res = requests.get(url,cookies=cookies,timeout=2)
        ports = res.json()['data']


        url = f"http://{ip}:8080/api/tree?q=$.status.lan.clients"
        res = requests.get(url,cookies=cookies)
        ips = res.json()['data']['status']['lan']['clients']
        ips = [ip['ip_address'] for ip in ips]
        devices = []
        for ip_lan in ips:
            for port in ports:
                if port['ip_address']==ip_lan:
                    try:
                        url = f"http://{ip}:{port['wan_port_start']}/isapiSdlc.dll?admin_config"
                        res = requests.get(url,timeout=1).json()
                        devices.append({'name':res['product'],'mac':res['macAddress'],'port':port['wan_port_start']})
                    except Exception as e:
                        try:
                            url = f'http://{ip}:{port["wan_port_start"]}/secure/unitinfo.xml'
                            res = requests.get(url,auth=('admin',''),timeout=1)
                            p = re.compile('<MAC>(.*?)</MAC>')
                            m = p.search(res.text)
                            mac = m.group(1)
                            out = {'name':'lantronix/600','mac':mac,'port':port['wan_port_start']}
                            devices.append(out)
                        except Exception as e:
                            pass
        if not devices:
            print(f'no radars found on {ip}')
        with lock:                
            signal['radar_ccus'] = unique_devices(devices)
    except Exception as e:
        print(e)
        signal['radar_ccus']=[]

def radar_check(signal,lock,log):
    with lock:
        devices =  copy.copy(signal['radar_ccus'])
        ip = signal['ip']
    ip = signal['ip'].split(':')[0]
    for device in devices:
        if '650' in json.dumps(device) or '656' in json.dumps(device):
            try:
                health_ip = f'http://{ip}:{device["port"]}/isapiSdlc.dll?device_health'
                matrix_ip = f'http://{ip}:{device["port"]}/isapiSdlc.dll?sensors=matrixfull'
                advance_ip = f'http://{ip}:{device["port"]}/isapiSdlc.dll?sensors=advance'
                config_ip = f'http://{ip}:{device["port"]}/isapiSdlc.dll?device_config'

                res = requests.get(matrix_ip,timeout=120)
                matrix = json.loads(res.text)
                res = requests.get(advance_ip,timeout=120)
                advance = json.loads(res.text)
                res = requests.get(config_ip,timeout=5)
                config = json.loads(res.text)
                device['version'] = config['firmwareVersion']
                device['serial'] = config['serialNumber']

                if config['biu'][2]['enabled']and config['biu'][3]['enabled']:
                    device['biu'] = '11 and 12'

                device['sensors'] = matrix['sensors']+advance['sensors']
            except Exception as e:
                print(e)
    with lock:
        signal['radar_ccus'] = devices
    return {
        'cog_id':signal['cog_id'],
        'devices':devices
    }

      

def unique_devices(devices):
    u_devices = []
    for device in devices:
        if not device['mac'] in [d['mac'] for d in u_devices]:
            u_devices.append(device)
    return u_devices

if __name__ == '__main__':
    RadarThread.db = 'data/test.json'
    with open(RadarThread.db,'r') as f:
        signals = json.load(f)

    if not os.path.isdir('data/logs'):
        os.mkdir('data/logs')
    outage_log = open('data/outage_log.txt','w')
    RadarThread.signals = signals
    RadarThread.one_run = True
    RadarThread.log = outage_log
    RadarThread.pause = True
    RadarThread.record = False
    RadarThread.stop_at = False
    RadarThread.data_root = 'data/'
    RadarThread.n_signals = len(RadarThread.signals)
    ma = queue.Queue(10)

    threads = []
    for thread in range(10):
        thread_i = RadarThread(ma)
        threads.append(thread_i)
        thread_i.start()

    for thread in threads:
        thread.join()

    threads[0].to_excel(no_time=True)
