import requests
import snmp
import re
import json
import threading
from threaded_update import UpdateThread
from power_thread import time_res
import copy
import os
import shutil
import datetime
import queue
import numpy as np
from requests.exceptions import ConnectTimeout, ReadTimeout




def n_modem_updaters():
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, ModemThread):
            i+=1
    return i

class ModemThread(UpdateThread):
    
    def __init__(
            self, 
            db,
            counter,
            stopper,
            q,
            pauser,
            **kwargs
        ):
        fn_list = [get_devices,time_res]
        self.timeout = 3
        super().__init__(
            db,
            fn_list,
            counter,
            stopper,
            q,
            pauser,
            self.timeout,
            self.signals,
            **kwargs
            )

def get_devices(network,lock,timeout,sig_db):
    # default values for failed requests
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

    ip = network['ip']
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        # Login and get cookies
        res = requests.post(url,data=data,timeout=timeout)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        # get modem info
        url = f"http://{ip}:8080/api/status/wan/devices"
        res = requests.get(url,cookies=cookies,timeout=timeout)
        device_data = res.json()['data']
        if res.status_code==401:
            return {'ip':ip,'modem':'not authorized'}

        # Set up standard query
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
        
        # Extract all features from previous two requests
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



        # find associated signal based on gps if it is working on modem
        with sig_db.lock:
            dist = [np.sqrt(
                ((float(signal['lat'])-lat)*10000)**2+((float(signal['long'])-lon)*10000)**2
                ) 
                for signal 
                in sig_db.data
            ]

        if lat==0 or min(dist)>4:
            network['intersection'] = 'cannot locate'
            network['cog_id'] = 0
            network['lat'] = 0
            network['long'] = 0
            # Find signal based on name if possible
            # http://172.22.4.118/maxprofile/accounts/loginWithPassword
            # ws://172.22.4.170/maxtime/api/mib/pubsub
            #         mibs
            # : 
            # [["MainStrt"], ["SecStrt"], ["CtrlId"], ["configValidationDescription"], ["configValidationSeverity"],…]
            # type
            # : 
            # "subscribe"

        else:
            ind = np.argmin(dist)
            with sig_db.lock:
                signal = sig_db.data[ind]

                # handle ips that have multiple signals, change their ip based 
                # on previous matching
                if len(signal['ip'].split(':'))>1:
                    for signal_i in sig_db.data[ind]:
                        if signal_i['ip'].split(':')[0]==signal['ip'].split(':')[0]:
                            signal_i['ip']=network['ip']+signal_i['ip'].split(':')[1]
                else:
                    signal['ip']=network['ip']

            network['intersection'] = signal['name']
            network['cog_id'] = signal['cog_id']
            network['lat'] = signal['lat']
            network['long'] = signal['long']

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

        network['modem'] = out_dict

        return {'ip':ip,'modem':out_dict}

    except ConnectTimeout as e:
        print(e)
        return {'ip':ip,'modem':'N/A'}
    except ReadTimeout as e:
        if timeout>120:
            return {'ip':ip,'modem':'bad connection'}
        else:
            return get_devices(network,lock,timeout+20,sig_db)
    
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
