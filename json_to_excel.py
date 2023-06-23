import os
import pandas as pd
import json
import io
import copy


def export_sig(signals):
    signals = copy.deepcopy(signals)
    meters = []
    for signal in signals:
        meters_i = signal.pop('meters')
        for meter in meters_i:
            meter['cog_id'] = signal['cog_id']
            meters.append(meter)

    df_sig = pd.DataFrame(signals)
    df_met = pd.DataFrame(meters)
    df_met['esi_id'] = df_met['esi_id'].astype(str)

    file = io.BytesIO()
    with pd.ExcelWriter(file) as writer:
        df_sig.to_excel(writer,'signals')
        df_met.to_excel(writer,'meters')

    file.seek(0,0)
    return file

def import_sig(file):
    sig_types = {
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
    }
    sig_na = {
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
    }

    met_types = {
        'esi_id':int,
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
    }
    met_na = {
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
    }
    signals = pd.read_excel(file.stream._file,'signals',na_values='-').fillna(sig_na).astype(sig_types)
    signals = list(signals.drop('Unnamed: 0',axis = 1).to_dict('index').values())
    meters = pd.read_excel(file.stream._file,'meters', na_values='-').fillna(met_na).astype(met_types)
    meters = list(meters.drop('Unnamed: 0',axis = 1).to_dict('index').values())
    for signal in signals:
        signal['meters'] = []
        for meter in meters:
            if meter.get('cog_id','') == signal['cog_id']:
                foo = meter.pop('cog_id')
                signal['meters'].append(meter)

    return signals


