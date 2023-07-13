import requests
import json
import dotenv
import power_meter
import os
import pandas

data_root = os.path.join(os.getenv('APPDATA'),'acid')
env_path = os.path.join(data_root,'.env')
dotenv.load_dotenv(env_path)
data_path_dir = os.environ['DATA_PATH']
data_path = os.path.join(data_path_dir,'power.json')
with open(data_path,'r') as f:
    data = json.load(f)

meters = data['Traffic Signals']
local_data_path = os.path.join(data_path_dir,'Traffic Signal Spreadsheets.xlsx')
local_data = pandas.read_excel(local_data_path,'GPS')

key = os.environ['GEOAPI']
for meter in meters:
    meter_obj = power_meter.PowerMeter(meter)
    req_str = meter_obj.name.replace(' ','+')

    req_str = f"https://api.opencagedata.com/geocode/v1/json?q={req_str}&key={key}&language=en&pretty=1"


    meter_obj.geocode = json.loads(requests.get(req_str).text)

    meter_local = local_data[local_data['COG_ID']==meter_obj.cog]

    meter_obj.local_data = meter_local.to_dict()
