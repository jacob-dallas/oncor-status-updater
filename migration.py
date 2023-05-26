import pandas as pd
import json
from power_meter import PowerMeter
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def migrate(filename, oncor=False):
    # migrate_1(filename)
    # migrate_2(filename)
    # if oncor:
    #     oncor_record(filename)
    match_esi(filename)


def migrate_1(json_file):
# convert data to better format
    data = pd.read_excel('Traffic Signal Spreadsheets.xlsx','ONCOR', converters={"ESI ID": str})

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
        data = json.load(f)['Traffic Signals']
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

    with open('power_cut.json','w') as f:
        data = json.dump(data,f,indent=1)

if __name__ == '__main__':
    cut_integrate('power.json','cut_devices.json')
