import numpy as np
import threading
import os
import shutil
import json
import copy
from json_to_excel import export_to_excel, import_from_excel
import pathlib

def channel_to_str(sensor):
    channel = sensor.get('channels',[])
    out = ''
    for c in channel:
        out += f'{int(c)},'
    sensor['channels']=out
    return sensor
def str_to_channel(channel_str):
    
    out = channel_str.split(',')
    out = [bool(x) for x in out]
    return out
# esi id not exporting correctly
class Signal():
    sheets = ['meters','sensors','radar_ccus']
    out_converters = [lambda x:x,channel_to_str,lambda x:x]
    relationship = [2,2,2]
    pk = 'cog_id'
    fk = ['cog_id','cog_id,radar_ccus.serial,radar_ccus.mac','cog_id']
    name = 'signals'
    in_converters=[{},{'channels':str_to_channel},{}]
    types = [
        {
            'cog_id':int,
            'ip':str,
            'name':str,
            'street':str,
            'zip_code':int,
            'signal_system':str,
            'cut_service_id':str,
            'cut_id':str,
            'modem_online':bool,
            'controller_online':bool,
            'controller_status':str,
            'updated_at':str,
            'n_ccu':str,
            'n_matrix':str,
            'n_advance':str,
        },
        {
            'cog_id':int,
            'esi_id':np.int64,
            'comment':str,
            'oncor_address':str,
            'address_sim':float,
            'status':str,
            'bbu':int,
            'owner':str,
            'pole_num':str,
            'checked':int,
            'number':str,
            'online_status':str
        },
        {
            'channels':str,
            'name':str,
            'type':str,
            'id':str,
            'serialNumber':str,
            'location':str,
            'description':str,
            'approach':str,
            'port':str,
            'cog_id':int,
            'serial':str,
            'mac':str,
        },
        {
            'serial':np.int64,
            'mac':str,
            'port':str,
            'version':float,
            'name':str,
            'cog_id':np.int64,
        }
    ]
    na_values = [
        {
            'cog_id':0,
            'ip':'0.0.0.0',
            'name':'-',
            'street':'-',
            'zip_code':00000,
            'signal_system':'-',
            'cut_service_id':'-',
            'cut_id':'-',
            'modem_online':False,
            'controller_online':False,
            'controller_status':'-',
            'updated_at':'-',
            'n_ccu':0,
            'n_matrix':0,
            'n_advance':0,
        },
        {
            'cog_id':10000,
            'esi_id':10443720000000000,
            'comment':'-',
            'oncor_address':'-',
            'address_sim':0.0,
            'status':'-',
            'bbu':0,
            'owner':'-',
            'pole_num':'-',
            'checked':0,
            'number':'-',
            'online_status':'-'
        },
        {
            'channels':'0,',
            'name':'foo',
            'type':1,
            'id':1,
            'serialNumber':1,
            'location':1,
            'description':1,
            'approach':1,
            'port':1,
            'cog_id':1,
            'serial':1,
            'mac':1,
        },
        {
            'serial':0,
            'mac':0,
            'port':0,
            'version':0,
            'name':'-',
            'cog_id':0,
        }
    ]
    def __init__(self,db=None,path=None):
        self.data=db
        self.path = path
        self.lock = threading.Lock()
        if path:
            if not os.path.exists(path):
                shutil.copy('db_template.json',path)
            with open(path,'r') as f:
                self.data=json.load(f)
    def get_data(self):
        with self.lock:
            data = copy.copy(self.data)
        return data
    def save_to_file(self):
        with self.lock:
            with open(self.path,'w') as f:
                json.dump(self.data,f,indent=4)
    def export(self,fields):
        with self.lock:
            file = export_to_excel(self)
        return file
    
    def save_and_bak(self):
        root_path = pathlib.Path(self.path).parent.absolute()
        with self.lock:

            shutil.copy(self.path,os.path.join(root_path,f'{self.name}.bak'))
        self.save_to_file()

class Network():
    sheets = ['clients','licenses','modem']
    out_converters = [lambda x:x,lambda x:x,lambda x:x]
    relationship = [2,2,1]
    pk = 'ip'
    # do not put foreign keys below or at same level as sheet

    fk = ['ip,modem.mac','ip,modem.mac','ip']
    name = 'networks'
    in_converters=[{},{},{}]
    types = [
        {
            "ip": str,
            "cog_id": int,
            "intersection": str,
            "lat": int,
            "long": int,
            "updated_at":str
        },
        {
            "mac": str,
            "ip_address": str,
            "modem.mac": str,
            "ip": str,
        },
        {
            '0':str,
            '1':str,
            '2':int,
            '3':int,
            "mac": str,
            "ip": str,
        },
        {
            "os_ver": str,
            "fw_ver": str,
            "device_name": str,
            "lat": int,
            "lon": int,
            "upgradeable": bool,
            "dbm": str,
            "sn": str,
            "model": str,
            "mac": str,
            "cpu": float,
            "temp": str,
            "ip": str,
        }
    ]
    na_values=[
        {
            "ip": "172.22.0.0",
            "cog_id": 0,
            "intersection": "cannot locate",
            "lat": 0,
            "long": 0,
            "updated_at":'0'
        },
        {
            "mac": "0",
            "ip_address": "192.168.0.0",
            "ip": "172.22.0.0",
            "modem.mac": "0",
        },
        {
            '0':'0',
            '1':'0',
            '2':0,
            '3':0,
            "ip": "172.22.0.0",
            "mac": "0",
        },
        {
            "os_ver": "-",
            "fw_ver": "-",
            "device_name": "-",
            "lat": 0.0,
            "lon": 0.0,
            "upgradeable": False,
            "dbm": "-",
            "sn": "0",
            "model": "-",
            "mac": "0",
            "cpu": 0.0,
            "temp": 0,
            "ip": '-',
        }
    ]
    def __init__(self,data=None,path=None) -> None:
        self.data=data
        self.path=path
        
        self.lock = threading.Lock()
        if path:
            if not os.path.exists(path):
                shutil.copy('modem_db_template.json',path)
            with open(path,'r') as f:
                self.data=json.load(f)

    def get_data(self):
        with self.lock:
            data = copy.copy(self.data)
        return data
    
    def save_to_file(self):
        with self.lock:
            with open(self.path,'w') as f:
                json.dump(self.data,f,indent=4)
    def export(self,fields):
        with self.lock:
            file = export_to_excel(self)
        return file
    
    def save_and_bak(self):
        root_path = pathlib.Path(self.path).parent.absolute()
        with self.lock:

            shutil.copy(self.path,os.path.join(root_path,f'{self.name}.bak'))
        self.save_to_file()