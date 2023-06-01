import json
import requests
import dotenv
import os
dotenv.load_dotenv()

redirect = 'https://cmss.city.dallastx.cod'
key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiJhYjM0YTUwMS0zMDJjLTQ5NzItYThlMi1lYmUxNDMzNGY5ZTAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8yOTM1NzA5ZS1jMTBjLTQ4MDktYTMwMi04NTJkMzY5Zjg3MDAvIiwiaWF0IjoxNjg1NDU2Mjc2LCJuYmYiOjE2ODU0NTYyNzYsImV4cCI6MTY4NTQ2MTM4MSwiYWNyIjoiMSIsImFpbyI6IkFUUUF5LzhUQUFBQWJxNGZEUmdacEhvemI1T21lU3hNbzBFenNTTUJ1dmFhYXZ5WGFJVURjNmFITzBHWEFNWmdNZ1lqbStsSFlZWk8iLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiYWIzNGE1MDEtMzAyYy00OTcyLWE4ZTItZWJlMTQzMzRmOWUwIiwiYXBwaWRhY3IiOiIxIiwiZmFtaWx5X25hbWUiOiJQYXZlbGthIiwiZ2l2ZW5fbmFtZSI6IkphY29iIiwiaXBhZGRyIjoiNjYuOTcuMTQ1LjY1IiwibmFtZSI6IlBhdmVsa2EsIEphY29iIiwib2lkIjoiNTE5ZWE1NmUtZWFkOC00ZTVkLTkyY2EtOWEyOGFlNzAyMTJjIiwib25wcmVtX3NpZCI6IlMtMS01LTIxLTEwODUwMzEyMTQtMTY3NzEyODQ4My03MjUzNDU1NDMtMjEwNDcxIiwicmgiOiIwLkFUY0FubkExS1F6QkNVaWpBb1V0TnAtSEFBR2xOS3NzTUhKSnFPTHI0VU0wLWVBM0FPay4iLCJzY3AiOiJVc2VyLlJlYWQiLCJzdWIiOiJ5cHVsa09PVEt3OGZXX0twbUZfVUVEQkliRmgyN2tieHNZTlZPVUFSTEpRIiwidGlkIjoiMjkzNTcwOWUtYzEwYy00ODA5LWEzMDItODUyZDM2OWY4NzAwIiwidW5pcXVlX25hbWUiOiJqYWNvYi5wYXZlbGthQGRhbGxhc2NpdHloYWxsLmNvbSIsInVwbiI6ImphY29iLnBhdmVsa2FAZGFsbGFzY2l0eWhhbGwuY29tIiwidXRpIjoiN1JKWkZjRXVQRVdVcE5jVkdXU0FBQSIsInZlciI6IjEuMCJ9.PPW-MuDQhbqYBvtKo94gU4Lg8OhpHtbFZr8AMTU0oAsH_E5_cCrMshif9HmVipnhyKK5DYF_sMmAuFH0Aqijwj1haiwcJv8XkoWK-p0uLsBLTxtAJFhzhK5wYuVZEtnPDuMB1llpJi8U-0q8yiHRSmYR-N9P0WcXwv8jK0Nmr3OsVLoecafsVUJcUPBFzY7_eiPm6yHeJU42ZSlObmhylWqAcf7P2uJS0kquyMYK3Zhj6uzx6kQUAjPyedtMjT4tk-g4fOuXpLPFissbMpkcnUVVSND-GEYU53fqNmj_6sXJ92J4U_-Atd_pzndmhjPyHqSQpzUScxLmtJRUdH0Uaw'

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



