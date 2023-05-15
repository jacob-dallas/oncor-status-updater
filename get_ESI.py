import pandas as pd
import json

def dict_list():

    data = pd.read_excel('Traffic Signal Spreadsheets.xlsx','ONCOR',converters={"ESI ID": str})

    ids = data['ESIID'].tolist()
    meter_nums = data['Devices_EBS'].tolist()

    meterlist = []
    for id, num in zip(ids,meter_nums):
        obj = {'esiid':id}
        meterlist.append(obj)

    return meterlist

if __name__ == '__main__':
    var = dict_list()
    print(json.dumps(var))