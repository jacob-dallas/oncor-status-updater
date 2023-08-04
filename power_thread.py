import threading
from pythonping import ping
from controller_snmp import controller_ping
from threaded_update import UpdateThread
from power_meter import PowerMeter
import datetime

def n_power_updaters():
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, PowerThread):
            i+=1
    return i


class PowerThread(UpdateThread):
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
    
    def __init__(
            self, 
            db,
            counter,
            stopper,
            q,
            pauser,
            **kwargs
        ):
        fn_list = [oncor,controller,time_res]
        super().__init__(
            db,
            fn_list,
            counter,
            stopper,
            q,
            pauser,
            **kwargs
            )



def oncor(signal,lock):
    try:
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

            # Begins the search web interface
            status = obj.http_get()

            obj.online_status = status

            with lock:
                signal['meters'][preffered_ind] = obj.__dict__

            obj.cog_id = signal['cog_id']
            res = obj.__dict__
    
        return res
    except Exception as e:
        print(e)
        return {'cog_id':signal['cog_id']}

def controller(signal,lock):
    try:
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
                controller_status = PowerThread.status_dict.get(str(status_code),'Free/Unregistered Status')
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
        return res
    except Exception as e:
        print(e)
        return {'cog_id':signal['cog_id']}

def time_res(signal,lock,*args):
    updated_at = str(datetime.datetime.now())
    res = {
        "cog_id":signal["cog_id"],
        'time':updated_at,
        "msg_id":'time'
    }
    with lock:
        signal["updated_at"] = updated_at
    return res