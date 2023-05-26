import json
import requests

redirect = 'https://cmss.city.dallastx.cod'
key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiJhYjM0YTUwMS0zMDJjLTQ5NzItYThlMi1lYmUxNDMzNGY5ZTAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8yOTM1NzA5ZS1jMTBjLTQ4MDktYTMwMi04NTJkMzY5Zjg3MDAvIiwiaWF0IjoxNjg1MDQyNzUyLCJuYmYiOjE2ODUwNDI3NTIsImV4cCI6MTY4NTA0NzE1NSwiYWNyIjoiMSIsImFpbyI6IkUyWmdZQkNVMDltdG5lVzdLRXZBa3FOSDhaUW1DMHRTYTlIRlJuY2VsL1MvdXJzU3MvUzZkczdLdEJmNTgzZnZaMitYTDR2TEFBPT0iLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiYWIzNGE1MDEtMzAyYy00OTcyLWE4ZTItZWJlMTQzMzRmOWUwIiwiYXBwaWRhY3IiOiIxIiwiZmFtaWx5X25hbWUiOiJQYXZlbGthIiwiZ2l2ZW5fbmFtZSI6IkphY29iIiwiaXBhZGRyIjoiNjYuOTcuMTQ1LjY1IiwibmFtZSI6IlBhdmVsa2EsIEphY29iIiwib2lkIjoiNTE5ZWE1NmUtZWFkOC00ZTVkLTkyY2EtOWEyOGFlNzAyMTJjIiwib25wcmVtX3NpZCI6IlMtMS01LTIxLTEwODUwMzEyMTQtMTY3NzEyODQ4My03MjUzNDU1NDMtMjEwNDcxIiwicmgiOiIwLkFUY0FubkExS1F6QkNVaWpBb1V0TnAtSEFBR2xOS3NzTUhKSnFPTHI0VU0wLWVBM0FPay4iLCJzY3AiOiJVc2VyLlJlYWQiLCJzdWIiOiJ5cHVsa09PVEt3OGZXX0twbUZfVUVEQkliRmgyN2tieHNZTlZPVUFSTEpRIiwidGlkIjoiMjkzNTcwOWUtYzEwYy00ODA5LWEzMDItODUyZDM2OWY4NzAwIiwidW5pcXVlX25hbWUiOiJqYWNvYi5wYXZlbGthQGRhbGxhc2NpdHloYWxsLmNvbSIsInVwbiI6ImphY29iLnBhdmVsa2FAZGFsbGFzY2l0eWhhbGwuY29tIiwidXRpIjoidjN1Slp1eTBKVU9PSEtiWm9SLVRBQSIsInZlciI6IjEuMCJ9.U5s1Nhlz8m3fxrsEzSlQHC7jo2J_BfTW18WE7cjgM4MJACXdhrUAadECnM5S_k-WRCvhq-3zqdWp4Jf5unWcSbd_nGJjnuo_ylQV11BVTdBCPSU7HyCAI6Tb9gfV8yswKRN8-9xuEiubam6JrkiU_HSwNRfuAUn34ovsJNrjLTYNSSuU0Pq_aMXXr6a6Yal5oWxsLH_2U_PNe05bSUZyKia-SC20suXRPM57cx_by9_gTLzOwAPJPNqHgDu-5JfQikTNpyyEbNwZ0nzakuxixr23_tpDNQSa2jIM_xM1DpXdvBJrXI5cBTEpxaEhDdyfMWlx7oZidWU3y6Im9H705Q'

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

if __name__ == '__main__':
    try:
        res = devices()
    except Exception as ex:
        print(ex)
        quit()
    print(res)
    data = json.loads(res.text)
    with open('cut_devices.json','w') as f:
        json.dump(data,f,indent=1)

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

# try this url for auth https://github.com/AzureAD/azure-activedirectory-library-for-python#microsoft-azure-active-directory-authentication-library-adal-for-python


