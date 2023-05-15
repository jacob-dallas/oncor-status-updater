import requests
from get_ESI import dict_list
import json

smt_url = "https://uatservices.smartmetertexas.net/15minintervalreads/"


params = {
    "trans_id":"311",
    "requestorID":"TRNAPI",
    "requesterType":"BUSINESS",
    "requesterAuthenticationID":"044634483",
    "startDate":"05/01/2023",
    "endDate":"05/02/2023",
    "deliveryMode":"JSON",
    "version":"L",
    "readingType":"C",
    "esiid": ['10443720009036789'],
    "SMTTermsandConditions":"Y"
    }

print(json.dumps(params))

response = requests.post(smt_url, json=params, auth=('TRNAPI','0rTkp64XsP$c*c280sn!'))
print(response.json())
print(response.status_code)