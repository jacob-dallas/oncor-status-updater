# a script to validate all esi ids
# need to get addresses and diff them
# need to find ids that are no longer active
# need to differentiate esi ids from signboards
# transition away from spreadsheets for inputs
# make output spreadsheets for regular intervals

import pandas as pd
import json
from power_meter import PowerMeter
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def spreadsheet_to_json():
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

    with open('power.json','w') as data_json:
        json.dump(data_dict,data_json,indent=1)

def validate_address(json_file):
    with open(json_file,'r') as file:
        data = json.load(file)

    service = Service(executable_path="chromedriver.exe")
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless=new')
    options.accept_insecure_certs=True
    driver = webdriver.Chrome(service=service, options=options)
    
    sig_list = []
    for signal in data['Traffic Signals']:
        sig = PowerMeter(signal)
        sig.verify_address(driver)
        sig_list.append(sig.to_dict())

    data['Traffic Signals'] = sig_list

    with open('new_power.json','w') as data_json:
        json.dump(data,data_json,indent=1)

if __name__ == '__main__':
    validate_address('power.json')