import requests
import json
import dotenv
import power_meter
import os
import pandas

dotenv.load_dotenv()

with open('new_power.json','r') as f:
    data = json.load(f)

meters = data['Traffic Signals']
local_data = pandas.read_excel('Traffic Signal Spreadsheets','GPS')

for meter in meters:
    key = os.environ['GEOAPI']
    meter_obj = power_meter.PowerMeter(meter)
    req_str = meter_obj.name.replace(' ','+')

    req_str = f"https://api.opencagedata.com/geocode/v1/json?q={req_str}&key={key}&language=en&pretty=1"


    meter_obj.geocode = json.loads(requests.get(req_str).text)

    meter_local = local_data[local_data['COG_ID']==meter_obj.cog]

    meter_obj.local_data = meter_local.to_dict()
