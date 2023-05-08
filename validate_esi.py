# a script to validate all esi ids
# need to get addresses and diff them
# need to find ids that are no longer active
# need to differentiate esi ids from signboards
# transition away from spreadsheets for inputs
# make output spreadsheets for regular intervals

import pandas as pd
import json

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
        "Device_ESB2":"meter_number_2",
        "Zip_code":"zip_code"
        }
    )

dms = data[data['device_type']=='DMS'].to_dict('index').values()
sig = data[data['device_type']=='SIG'].to_dict('index').values()
sch = data[data['device_type']=='SCH'].to_dict('index').values()
wrn = data[data['device_type']=='WRN'].to_dict('index').values()
slt = data[data['device_type']=='STREET LIGHTS'].to_dict('index').values()

data_dict = {'DMS':list(dms),'School Flashers':list(sch),'Flasher':list(wrn),'Street Lights':list(slt),'Traffic Signals':list(sig)}

with open('power.json','w') as data_json:
    json.dump(data_dict,data_json,indent=1)