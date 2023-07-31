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
import numpy as np
from requests.exceptions import ConnectTimeout, ReadTimeout
from json_to_excel import export_sig



def n_modem_updaters():
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, ModemThread):
            i+=1
    return i
def stop_modem():
    for thread in threading.enumerate():
        if isinstance(thread, ModemThread):
            thread.set_stop(True)
    

# add update schedule

class ModemThread(threading.Thread):
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

    @property
    def n_modems(self) -> int:
        return len(self.modems)
    
    def set_stop(self,value = False):
        self.stop = value
    
    # work on updating database and making a manual update feature
    def run(self):
        while True:
            
            with self.lock:
                self.i = ModemThread.last_complete_entry
                if self.i > len(self.modems)-1:
                    if self.one_run:
                        stop_modem()
                    ModemThread.last_complete_entry = 0
                    self.save_and_bak()
                    self.i = ModemThread.last_complete_entry
                    # add a function in here to search for a specific meter
                else:
                    ModemThread.last_complete_entry += 1
                modem = ModemThread.modems[self.i]
            if self.stop:
                break

            

            res = get_devices(modem,self.lock,self.log,3)
            if not self.pause:
                self.add_to_queue(res)
            res = time_res(modem,self.lock,self.log)
            if not self.pause:
                self.add_to_queue(res)

                

            if self.record:
                with self.lock:
                    exist = getattr(self,'record_time',False)
                    if exist:
                        expired = ModemThread.record_time<datetime.datetime.now()
                        if expired:
                            self.to_excel()
                            ModemThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))
                    else:
                        ModemThread.record_time = datetime.datetime.now()+datetime.timedelta(hours=float(self.record))

            if self.stop_at and ModemThread.stop_at<datetime.datetime.now() and not self.stop:
                print('stopping now!')
                with ModemThread.lock:
                    stop_modem()
                    ModemThread.last_complete_entry = 0
                self.save_and_bak()


            with self.lock:
                percent_complete = self.i/len(self.modems)*100
                print(f'{percent_complete:.2f}%')
    
    
    def add_to_queue(self,res):
        self.queue.put(json.dumps(res))

    def save_and_bak(self):
        shutil.copy(self.db_modem,os.path.join(self.data_root,'modems.bak'))
        with open(self.db_modem,'w') as f:
            json.dump(self.modems,f,indent=4)
        shutil.copy(self.db,os.path.join(self.data_root,'signals.bak'))
        with open(self.db,'w') as f:
            json.dump(self.signals,f,indent=4)

    def to_excel(self,no_time=False):
        file = export_sig(ModemThread.signals)
        log_dir = os.path.join(ModemThread.data_root,'logs')
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



def get_devices(modem,lock,log,timeout):
    ip = modem['ip']
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        res = requests.post(url,data=data,timeout=timeout)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        url = f"http://{ip}:8080/api/config/firewall/portfwd/"

        res = requests.get(url,cookies=cookies,timeout=timeout)
        if res.status_code==401:
            return {'ip':ip,'modem':'not authorized'}
        ports = res.json()['data']

        url = f"http://{ip}:8080/api/status/wan/devices"
        res = requests.get(url,cookies=cookies,timeout=timeout)
        device_data = res.json()['data']

        null_gps = {
            'fix':{
                'latitude':{
                    'degree':0,
                    'minute':0,
                    'second':0,
                },
                'longitude':{
                    'degree':0,
                    'minute':0,
                    'second':0,
                },
            }
        }
        
        url = f"http://{ip}:8080/api/tree"
        res = requests.get(
            url,
            cookies=cookies,
            params={
                'q':[

                    '$.status.lan.clients',
                    '$.status.product_info.product_name',
                    '$.status.product_info.mac0',
                    '$.status.system.cpu',
                    '$.status.system.modem_temperature',
                    '$.status.wan.primary_device',
                    '$.status.fw_info',
                    '$.status.gps.fix.latitude',
                    '$.status.gps.fix.longitude',
                    '$.status.feature.db',
                ]
            }
            ).json()
        status = res['data']['status']

        licenses = status['feature'].get('db',[])

        fw_info = status['fw_info']
        lat_lon = status.get('gps',null_gps)['fix']
        os_ver = f"{fw_info['major_version']}.{fw_info['minor_version']}.{fw_info['patch_version']}"
        lat = lat_lon['latitude']['degree']+lat_lon['latitude']['minute']/60+lat_lon['latitude']['second']/3600
        lon = lat_lon['longitude']['degree']-lat_lon['longitude']['minute']/60-lat_lon['longitude']['second']/3600
        primary_device = status.get('wan',{'foo':'bar'}).get('primary_device','foo')
        if primary_device=='foo':
            print(ip)
        device_info = device_data.get(primary_device)
        if device_info:
            upgradeable = device_info['ob_upgrade']['check']=='update_available'
            firmware = device_info['ob_upgrade'].get('fw_info',{'upgrade_pkg_version':'0.0.0'})['upgrade_pkg_version']
            signal_strength = device_info['status']['signal_backlog'][0]['dbm']
            serial = device_info['info']['serial']
        else:
            url = f'http://{ip}:8080/api/microstatus'
            res = requests.get(url,cookies=cookies).json()
            for mdm in res['data']:
                if mdm['connection_state']=='connected' or mdm['signal_strength']>50:
                    primary_device = f'mdm-{mdm["uid"]}'
            device_info = device_data.get(primary_device)
            upgradeable = device_info['ob_upgrade']['check']=='update_available'
            firmware = device_info['ob_upgrade'].get('fw_info',{'upgrade_pkg_version':'0.0.0'})['upgrade_pkg_version']
            signal_strength = device_info['status']['signal_backlog'][0]['dbm']
            serial = device_info['info']['serial']
        model = status['product_info']['product_name']
        mac = status['product_info']['mac0']
        cpu_usage = status['system']['cpu']['user']+status['system']['cpu']['nice']+status['system']['cpu']['system']
        temp = status['system'].get('modem_temperature',0)

        # http://172.22.4.118/maxprofile/accounts/loginWithPassword
        # ws://172.22.4.170/maxtime/api/mib/pubsub
        #         mibs
        # : 
        # [["MainStrt"], ["SecStrt"], ["CtrlId"], ["configValidationDescription"], ["configValidationSeverity"],…]
        # type
        # : 
        # "subscribe"

        with lock:
            dist = [np.sqrt(((float(signal['lat'])-lat)*10000)**2+((float(signal['long'])-lon)*10000)**2) for signal in ModemThread.signals]

        if lat==0 or min(dist)>4:
            modem['intersection'] = 'cannot locate'
            modem['cog_id'] = 0
            modem['lat'] = 0
            modem['long'] = 0
        else:

            ind = np.argmin(dist)
            with lock:
                signal = ModemThread.signals[ind]
                if len(signal['ip'].split(':'))>1:
                    for signal_i in ModemThread.signals:
                        if signal_i['ip'].split(':')[0]==signal['ip'].split(':')[0]:
                            signal_i['ip']=modem['ip']+signal_i['ip'].split(':')[1]
                else:

                    signal['ip']=modem['ip']

            modem['intersection'] = signal['name']
            modem['cog_id'] = signal['cog_id']
            modem['lat'] = signal['lat']
            modem['long'] = signal['long']

        out_dict = {
            'clients':status['lan']['clients'],
            'os_ver':os_ver,
            'fw_ver':firmware,
            'device_name':primary_device,
            'lat':lat,
            'lon':lon,
            'upgradeable':upgradeable,
            'dbm':signal_strength,
            'sn':serial,
            'model':model,
            'mac':mac,
            'cpu':cpu_usage,
            'temp':temp,
            'licenses':licenses

        }

        modem['modem'] = out_dict

        return {'ip':ip,'modem':out_dict}

    except ConnectTimeout as e:
        print(e)
        return {'ip':ip,'modem':'N/A'}
    except ReadTimeout as e:
        if timeout>120:
            return {'ip':ip,'modem':'bad connection'}
        else:
            return get_devices(modem,lock,log,timeout+20)
    
    except Exception as e:
        print(e)
        return {'ip':ip,'modem':'N/A'}

if __name__ == '__main__':
    ModemThread.db = 'data/test.json'
    with open(ModemThread.db,'r') as f:
        signals = json.load(f)
    ModemThread.db_modem = 'data/modem.json'
    with open(ModemThread.db_modem,'r') as f:
        modems = json.load(f)

    if not os.path.isdir('data/logs'):
        os.mkdir('data/logs')
    outage_log = open('data/outage_log.txt','w')
    ModemThread.signals = signals
    ModemThread.modems = modems
    ModemThread.one_run = True
    ModemThread.log = outage_log
    ModemThread.pause = True
    ModemThread.record = False
    ModemThread.stop_at = False
    ModemThread.data_root = 'data/'
    ModemThread.n_signals = len(ModemThread.signals)
    ma = queue.Queue(10)

    threads = []
    for thread in range(10):
        thread_i = ModemThread(ma)
        threads.append(thread_i)
        thread_i.start()

    for thread in threads:
        thread.join()

    threads[0].to_excel(no_time=True)
