import json
import requests
key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiJhYjM0YTUwMS0zMDJjLTQ5NzItYThlMi1lYmUxNDMzNGY5ZTAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8yOTM1NzA5ZS1jMTBjLTQ4MDktYTMwMi04NTJkMzY5Zjg3MDAvIiwiaWF0IjoxNjg0NzY4NTkyLCJuYmYiOjE2ODQ3Njg1OTIsImV4cCI6MTY4NDc3NDA2OSwiYWNyIjoiMSIsImFpbyI6IkFUUUF5LzhUQUFBQXRWWk8xWFFVc292bWRpRXowOEVHTmJsZlROQURjb0VSSnJlZWpsc1pMK3dMd052YTBxNEVEdklqbDZrVjZUNHMiLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiYWIzNGE1MDEtMzAyYy00OTcyLWE4ZTItZWJlMTQzMzRmOWUwIiwiYXBwaWRhY3IiOiIxIiwiZmFtaWx5X25hbWUiOiJQYXZlbGthIiwiZ2l2ZW5fbmFtZSI6IkphY29iIiwiaXBhZGRyIjoiNjYuOTcuMTQ1LjY0IiwibmFtZSI6IlBhdmVsa2EsIEphY29iIiwib2lkIjoiNTE5ZWE1NmUtZWFkOC00ZTVkLTkyY2EtOWEyOGFlNzAyMTJjIiwib25wcmVtX3NpZCI6IlMtMS01LTIxLTEwODUwMzEyMTQtMTY3NzEyODQ4My03MjUzNDU1NDMtMjEwNDcxIiwicmgiOiIwLkFUY0FubkExS1F6QkNVaWpBb1V0TnAtSEFBR2xOS3NzTUhKSnFPTHI0VU0wLWVBM0FPay4iLCJzY3AiOiJVc2VyLlJlYWQiLCJzdWIiOiJ5cHVsa09PVEt3OGZXX0twbUZfVUVEQkliRmgyN2tieHNZTlZPVUFSTEpRIiwidGlkIjoiMjkzNTcwOWUtYzEwYy00ODA5LWEzMDItODUyZDM2OWY4NzAwIiwidW5pcXVlX25hbWUiOiJqYWNvYi5wYXZlbGthQGRhbGxhc2NpdHloYWxsLmNvbSIsInVwbiI6ImphY29iLnBhdmVsa2FAZGFsbGFzY2l0eWhhbGwuY29tIiwidXRpIjoiVWsyNUxtcjBHVTJFc2dRMUhhWWVBQSIsInZlciI6IjEuMCJ9.XpYezS4oWrH1TRfHUT04InO0vFQAT2wup_QRrDarztbruNwtAOU2R8AtR45K20Q0y2jkBArVmtugDX_E2fTleh-W-cW0Ieki0P5ioep03F9i-MjwR49FZDEBrbUT1TqGAnUJ9iaXDcN9-dqwgd6pWwdYnbX0QcJb83GCFp43kbngycD_4SNTyLwuqQ5WKxPEMv5DeL16MpHLAIGstMmLULcsq_U3t02PBQ7kqTMuD-FHN3SnRf7owoGP3cMm33f2s7dUGSczh7zX6vVYdHrgWbZLX1HD3qmJf-u2rG5n-TMngRM9a-J5cx5lshLWBHgO9HwrN0YaKRn5pzqmoR2giw'
body = {
    'username':'jacob.pavelka@dallascityhall.com',
    'password':'Yzdf9H6wa6sAiJ61234'
}

# url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/auth/login'
# res = requests.post(url,json=body,verify=False)

url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/alarms'
res = requests.get(url,verify='other.cer',headers={'x-access-token':key},params={'timestampFrom':"2023-05-21T07:00:00.000Z",'timestampTo':'2023-05-22T07:00:00.000Z'})

# url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/apiInfo'
# res = requests.get(url,verify=False)
print(res)
data = json.loads(res.text)
for alarm in data['alarms']:
    if not alarm['cleared']:
        print(alarm['name'],'    ',alarm['created'],'        ',alarm['severity'])
print(data)