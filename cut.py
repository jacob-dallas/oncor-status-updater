import json
from dotenv import load_dotenv
import os
data_root = os.path.join(os.getenv('APPDATA'),'acid')
env_path = os.path.join(data_root,'.env')
load_dotenv(env_path)

redirect = 'https://cmss.city.dallastx.cod'

key = os.environ['x-access-key']
def alarms():

    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/alarms'
    res = requests.get(
        url,
        verify='other.cer',
        headers={'x-access-token':key},
        params={
            'timestampFrom':"2023-05-21T07:00:00.000Z",
            'timestampTo':'2023-05-22T07:00:00.000Z'
        }
    )
    return res


def devices():
    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/devices'
    res = requests.get(
        url,
        verify='other.cer',
        headers={'x-access-token':key},
        params={
            'timestampFrom':"2023-05-21T07:00:00.000Z",
            'timestampTo':'2023-05-22T07:00:00.000Z'
        }
    )
    return res

def notifications():
    # there are none
    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/notifications'
    res = requests.get(
        url,
        verify='other.cer',
        headers={'x-access-token':key},
        params={
            'timestampFrom':"2023-05-21T07:00:00.000Z",
            'timestampTo':'2023-05-22T07:00:00.000Z'
        }
    )
    return res

def devices(key,fields=''):
    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/devices'

    res = requests.get(
        url,
        verify='other.cer',
        headers={'x-access-token':key}
    )
    if res.status_code ==401:
        raise Exception('you are not authorized')
    return res

def auth(name,pwd):

    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/auth/login'

    body = {
        'username':name,
        'password':pwd
    }

    res = requests.post(
        url,
        verify='other.cer',
        json=body
    )
    return res

def swagger(key):
    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/api.json'

    res = requests.get(
        url,
        verify='other.cer',
        headers={'x-access-token':key}
    )

    return res

def auth_AAD():

    client_id = "ab34a501-302c-4972-a8e2-ebe14334f9e0"
    alt_client_id = "b9061727-30d0-4832-be26-ed4d35776727"
    response_type = 'code'
    redirect_url = 'http://127.0.0.1:5000/auth'
    alt_redirect_url = 'https://cmss.city.dallastx.cod'

    ms_url = f"https://login.microsoftonline.com/common/oauth2/authorize?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_url}"
    res = requests.get(
        'https://login.microsoftonline.com/common/oauth2/authorize',
        params={
            'response_type': response_type,
            'client_id':client_id,
            'redirect_uri':alt_redirect_url
        }
    )

if __name__ == '__main__':
    username = os.environ['USERNAME']
    pwd = os.environ['PWD']
    res = auth(username,pwd)
    print(res.text)
















    # try:
    #     res = devices()
    # except Exception as ex:
    #     print(ex)
    #     quit()
    # print(res)
    # data = json.loads(res.text)
    # with open('cut_devices.json','w') as f:
    #     json.dump(data,f,indent=1)

# location is a feature collection that contains a feature. the feature is gps coord. I imagine other features are possible too
# device type is traffic signal controller, and that device is in the traffic signal group
# status 50 is unknown and 10 is ok code 40 is comm fail?.
# state and healthscore are varaibles that are not set
# interapplicationid is cogid
# smartobjects contain a lot of data. status is one of them. operational status 
# too. traffic signal groups and lane configuration are present but do not have 
# values that can be seen. possibly they are controlled by the resource type key. they have movement state value too. traffic signal pattern, alarm code, smart object groups and smart object group statuses
# TxDOT camera and message signs are other device types. they are in txdot camera and message sign category. I think the other things that could be in this category are like bbus and stuff
# smartobjecttypes and services are confusing to me still



