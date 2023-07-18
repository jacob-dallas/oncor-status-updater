import pandas as pd
import json
from power_meter import PowerMeter
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from itertools import compress
import os
import dotenv

data_root = os.path.join(os.getenv('APPDATA'),'acid')
env_path = os.path.join(data_root,'.env')
dotenv.load_dotenv(env_path)
data_path_dir = os.environ['DATA_PATH']

spreadsheet = os.path.join(data_path_dir,'Traffic Signal Spreadsheets.xlsx')

def migrate(filename, oncor=False):
    # migrate_1(filename)
    # migrate_2(filename)
    # if oncor:
    #     oncor_record(filename)
    match_esi(filename)


def migrate_1(json_file):
# convert data to better format

    data = pd.read_excel(spreadsheet,'ONCOR', converters={"ESI ID": str})

    data = data.drop([
        'ESI ID', 
        'COGID.1', 
        'ESI_Short',
        'ESI_Shop',
        'Address_EBS',
        'OriginalAddressEBS',
        'Match_addr',
        'Status', 
        'Status time'
        ],axis=1)

    data['Matching_ESI'] = data['Matching_ESI'].apply(lambda x: bool(x),)

    data = data.rename(
        columns={
            "ADDRESS":"street",
            "COGID":"cog_id",
            "ESIID":"esi_id",
            "Signal_Name":"name",
            "Matching_ESI":"esi_match",
            "DeviceType":"device_type",
            "Devices_EBS":"meter_number",
            "NumberofDevices":"num_meters",
            "Device_EBS2":"meter_number_2",
            "Zip_code":"zip_code",
            "Comment":"comment"
            }
        )

    data = data.fillna({'meter_number_2':'-','comment':'-'})

    dms = data[data['device_type']=='DMS'].to_dict('index').values()
    sig = data[data['device_type']=='SIG'].to_dict('index').values()
    sch = data[data['device_type']=='SCH'].to_dict('index').values()
    wrn = data[data['device_type']=='WRN'].to_dict('index').values()
    slt = data[data['device_type']=='STREET LIGHTS'].to_dict('index').values()

    data_dict = {'DMS':list(dms),'School Flashers':list(sch),'Flasher':list(wrn),'Street Lights':list(slt),'Traffic Signals':list(sig)}

    with open(json_file,'w') as data_json:
        json.dump(data_dict,data_json,indent=1)



def migrate_2(json_file):
    with open(json_file,'r') as file:
        data = json.load(file)
    meters = data['Traffic Signals']
    
    for meter in meters:
        meter['meters'] = []
        if isinstance(meter['meter_number'],str):
            meter['meters'].append(meter['meter_number'])
        if meter['meter_number_2']!= '-':
            meter['meters'].append(meter['meter_number_2'])

        meter.pop('meter_number')
        meter.pop('meter_number_2')
        meter.pop('num_meters')

        if meter['zip_code'] > 0:
            meter['zip_code'] = int(meter['zip_code'])
        else:
            meter['zip_code'] = 11111

    with open(json_file,'w') as data_json:
        json.dump(data,data_json,indent=1)


def oncor_record(json_file):
    with open(json_file,'r') as file:
        data = json.load(file)

    service = Service(executable_path="chromedriver.exe")
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless=new')
    options.accept_insecure_certs=True
    driver = webdriver.Chrome(service=service, options=options)

    for signal in data['Traffic Signals']:
        sig = PowerMeter(signal)
        sim = sig.verify_address(driver)
        signal["oncor_address"] = sig.oncor_address
        signal["status"] = sig.status
        signal["address_sim"] = sig.address_sim

    with open(json_file,'w') as data_json:
        json.dump(data,data_json,indent=1)

    driver.quit()

def match_esi(json_file):
    with open(json_file,'r') as file:
        data = json.load(file)

    meters = data['Traffic Signals']
    for meter in meters:
        meter['old_esi'] = []

    for meter in meters:
        if meter['status'] != 'registered':
            match_count = 0
            for sub_meter in meters:
                if (meter['cog_id']==sub_meter['cog_id'] and meter['esi_id']!=sub_meter['esi_id']):
                    match_count +=1
                    sub_meter['old_esi'].append(meter['esi_id'])
                    meter['delete']=True
            if match_count==0:
                meter['status'] = 'unregistered with no replacement'
                meter['delete']=False
        else:
            meter['delete']=False

    
    new_meters = []
    for meter in meters:
        if not meter['delete']:
            new_meters.append(meter)

    data['Traffic Signals'] = new_meters

    with open(json_file,'w') as data_json:
        json.dump(data,data_json,indent=1)

def cut_integrate(json_file,cut_file):
    with open(json_file,'r') as f:
        data = json.load(f)
    with open(cut_file,'r') as f:
        cut = json.load(f)['devices']

    for signal in data:
        for cut_signal in cut:

            try:
                if int(cut_signal['interApplicationId'])==signal['cog_id']:
                    signal['cut_service_id'] = cut_signal['serviceId']
                    signal['cut_id'] = cut_signal['id']
            except KeyError:
                continue
    print('finished')

    with open(json_file,'w') as f:
        json.dump(data,f,indent=1)

def ago_ip_integrate(json_file):
    # cut down to one esi and meter number, include other relevant info
    signals_out = []
    with open(json_file,'r') as f:
        data = json.load(f)['Traffic Signals']

    ago_data = pd.read_excel(
        'ElectricMetersAGOL_06012023.xlsx',
        sheet_name='ElectricMetersAGOL_06012023',
        na_values='-',
    )

    ip_data = pd.read_excel(
        spreadsheet,
        sheet_name="Intersections",
        header=4,
        na_values='-',

    )

    ago_data = ago_data[ago_data['El_Device_Type']=="SIG"].fillna('-')
    ip_data = ip_data.fillna('-')
    for meter in data:
        
        ip_sig = ip_data[ip_data["COG ID"]==meter["cog_id"]] #int-int
        if ip_sig.empty:
            raise Exception(f'no associated IP {meter["cog_id"]}')
        ago_sig = ago_data[ago_data["COG_ID"]==meter["cog_id"]] #float-int
        if ago_sig.empty:
            print(f'no associated ago {meter["cog_id"]}')
            continue
        signal = {
            "cog_id":meter["cog_id"],
            "ip":ip_sig['IP Address'].values[0],
            "name":meter["name"],
            "street":meter["street"],
            "zip_code":meter["zip_code"],
            "signal_system":ip_sig["Signal System"].values[0]
        }

        meter.pop('cog_id')
        meter.pop('name')
        meter.pop('street')
        meter.pop('zip_code')
        meter.pop('device_type')
        meter.pop('esi_match')
        meter.pop('meters')
        meter.pop('old_esi')
        meter.pop('delete')
        meters = []

        # if the esi we have isnt in maria's list, just delete it. it is 
        # probably old
        esi_from_ago = ago_sig['ESI_Short'].to_list()
        esi_from_ago = [str(int(x)) for x in esi_from_ago]
        esi_id = str(meter.get('esi_id','0000000'))[-7:]
        if not esi_id in esi_from_ago:
            meter['esi_id'] = '0000000'

        # get all esi accounts from maria's list and put them on the same signal 
        # object
        for i,meter_b in ago_sig.iterrows():
            # 1784 has two active accounts
            # if one of maria's esi accounts matches ours, just replace our data 
            if int(esi_id)==int(meter_b['ESI_Short']): #int(str)-int(float)
                meter['bbu']=meter_b["BBUPresent"]
                meter['owner']=meter_b["Department"]
                meter['pole_num']=meter_b["Pole_Number"]
                meter['checked']=meter_b["Checked"]
                meter['comment']=meter_b["Comment"]
                meter['number']=meter_b["Meter_Number"]
            # otherwise make a new account object. the accounts comments are 
            # included so each signal can be narrowed down to having one account
            else:
                meter = {
                    'esi_id':int(f'1044372{int(meter_b["ESI_Short"]):010}'),
                    'bbu':meter_b["BBUPresent"],
                    'owner':meter_b["Department"],
                    'pole_num':meter_b["Pole_Number"],
                    'checked':meter_b["Checked"],
                    'comment':meter_b["Comment"],
                    'number':meter_b["Meter_Number"],
                    'oncor_address':'-',
                    'address_sim':1,
                }
            meters.append(meter)
        signal['meters']=meters

        signals_out.append(signal)

    # get a list of unique identifiers (cog_ids) for comparing later
    cog_ids = [x['cog_id'] for x in signals_out]

    # check if any uids from ip data do not exist in our data, add if they are 
    # missing from our data but do not include meter info yet
    for i, signal in ip_data.iterrows():
        if str(signal['COG ID']) =='-':
            continue
        if not (str(signal['COG ID']) in str(cog_ids)):
            signal_dict = {
                "meters":[],
                "cog_id":signal["COG ID"],
                "ip":signal['IP Address'],
                "name":signal["Intersection Name"],
                "signal_system":signal["Signal System"]
            }
            signals_out.append(signal_dict)

    # remake uid list because new ones were added
    
    cog_ids = [x['cog_id'] for x in signals_out]
    for i, signal in ago_data.iterrows():
        # check if there are any uids in ago data that are not in existing data.
        # If so, add them to the list. there shouldnt be many.
        tempcog = 100000
        if not signal["COG_ID"] in cog_ids:
            if signal["ESI_Short"] == '-':
                signal["ESI_Short"] = 0
            if signal["COG_ID"] == '-':
                signal["COG_ID"] = tempcog
                tempcog +=1
            signal_dict = {
                "meters":[{
                    'esi_id':int(f'1044372{int(signal["ESI_Short"]):010}'),
                    'bbu':signal["BBUPresent"],
                    'owner':signal["Department"],
                    'pole_num':signal["Pole_Number"],
                    'checked':signal["Checked"],
                    'comment':signal["Comment"],
                    'number':signal["Meter_Number"],
                    'oncor_address':'-',
                    'address_sim':1,
                }],
                "cog_id":int(signal["COG_ID"]),
                "ip":'0.0.0.0',
                "name":signal["Loc_Name"],
                "signal_system":"-",
                "street":signal["Act_Service_Address"],
                "zip_code":signal["ZIPCode"]
            }
            signals_out.append(signal_dict)
            cog_ids.append(signal_dict['cog_id'])

        # if uid is already listed, make sure this esi and meter is associated 
        # with it
        else:
            # at this point all meters existing in the data should have been 
            # updated if they match ago or removed if they were not included 
            # in ago. if a signal doesn't have a meter in our data but has one 
            # in ago, this loop will add it to our data
            ind = cog_ids.index(signal['COG_ID'])
            sig_out = signals_out[ind]
            esi_list = [str(x['esi_id'])[-7:] for x in sig_out["meters"]]
            if signal['ESI_Short']=='-':
                signal['ESI_Short'] = 0
            if not str(int(signal['ESI_Short'])).zfill(7) in esi_list:
                meter = {
                    'esi_id':int(f'1044372{str(int(signal["ESI_Short"])).zfill(10)}'),
                    'bbu':signal["BBUPresent"],
                    'owner':signal["Department"],
                    'pole_num':signal["Pole_Number"],
                    'checked':signal["Checked"],
                    'comment':signal["Comment"],
                    'number':signal["Meter_Number"],
                    'oncor_address':'-',
                    'address_sim':1,
                }
                sig_out["meters"].append(meter)

    with open(json_file,'w') as f:
        json.dump(signals_out,f,indent=1)

def add_loc(json_file,test_file):
    with open(json_file,'r') as f:
        data = json.load(f)
    data_add = pd.read_excel(spreadsheet,'SignalDatainGIS',skiprows=2)
    for signal in data:
        if (signal['cog_id'] in data_add['COG_ID'].values):
            signal['lat']=data_add[data_add['COG_ID']==signal['cog_id']]['LAT'].values[0]
            signal['long']=data_add[data_add['COG_ID']==signal['cog_id']]['LONG'].values[0]
        else:
            signal['lat']=0
            signal['long']=0
    
    with open(test_file,'w') as f:
        json.dump(data,f,indent=3)

if __name__ == '__main__':
    power_path = os.path.join(data_path_dir,'power.json')
    test_path = os.path.join(data_path_dir,'test.json')
    add_loc(power_path,test_path)

    # old spreadsheet is at least older than 7.2022
    # i need to find a meter that says it is working but actually isnt
    # i can go look back at parthas messages
    