import requests
import re
import json
import threading
from threaded_update import UpdateThread
from power_thread import controller, time_res
import copy
import os
import queue


def n_radar_updaters():
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, RadarThread):
            i+=1
    return i


class RadarThread(UpdateThread):
    
    def __init__(self,db,counter,stopper,q,pauser,**kwargs):
        fn_list = [radar_check,controller,time_res]
        super().__init__(
            db,
            fn_list,
            counter,
            stopper,
            q,
            pauser,
            **kwargs
        )


def radar_check(signal,lock):
    # Safely Aquire IP
    with lock:
        ip = signal['ip']

    ip = signal['ip'].split(':')[0]

    url = f"http://{ip}:8080/login/"

    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }

    try:
        # Login Request
        res = requests.post(url,data=data,timeout=5)

        # Combine Cookies for later use
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        # Get firewall and client data
        url = f"http://{ip}:8080/api/config/firewall/portfwd/"
        res = requests.get(url,cookies=cookies,timeout=5)
        ports = res.json()['data']

        url = f"http://{ip}:8080/api/tree?q=$.status.lan.clients"
        res = requests.get(url,cookies=cookies)
        ips = res.json()['data']['status']['lan']['clients']
        ips = [ip['ip_address'] for ip in ips]
        if not ('192.168.0.6' in ips):
            ips.append('192.168.0.6')
        devices = []

        # Determine if any clients are radar ccu's
        for ip_lan in ips:
            for port in ports:
                if port['ip_address']==ip_lan:
                    # See if radar is a 650 or 656
                    try:
                        url = f"http://{ip}:{port['wan_port_start']}/isapiSdlc.dll?admin_config"
                        res = requests.get(url,timeout=10).json()
                        devices.append({'name':res['product'],'mac':res['macAddress'],'port':port['wan_port_start']})
                    except Exception as e:
                        # If not, see if it is a 600
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

                res = requests.get(config_ip,timeout=5)
                config = json.loads(res.text)
                device['version'] = config['firmwareVersion']
                device['serial'] = config['serialNumber']

                if config['biu'][2]['enabled']and config['biu'][3]['enabled']:
                    device['biu'] = '11 and 12'
                    
                res = requests.get(matrix_ip,timeout=120)
                matrix = json.loads(res.text)
                res = requests.get(advance_ip,timeout=120)
                advance = json.loads(res.text)

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
