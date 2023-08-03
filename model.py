import numpy as np

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

class Signal():
    sheets = ['meters','sensors','radar_ccus']
    out_converters = [lambda x:x,channel_to_str,lambda x:x]
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
    def __init__(self,db=None):
        self.data=db

class Network():
    sheets = ['meters','sensors','radar_ccus']
    out_converters = [lambda x:x,channel_to_str,lambda x:x]
    pk = 'cog_id'
    fk = ['cog_id','cog_id,radar_ccus.serial,radar_ccus.mac','cog_id']
    name = 'signals'
    in_converters=[{},{'channels':str_to_channel},{}]