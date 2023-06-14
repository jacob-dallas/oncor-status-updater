import requests
from get_ESI import dict_list
import json

# smt_url = "https://uatservices.smartmetertexas.net/15minintervalreads/"


# params = {
#     "trans_id":"311",
#     "requestorID":"TRNAPI",
#     "requesterType":"BUSINESS",
#     "requesterAuthenticationID":"044634483",
#     "startDate":"05/01/2023",
#     "endDate":"05/02/2023",
#     "deliveryMode":"JSON",
#     "version":"L",
#     "readingType":"C",
#     "esiid": ['10443720009036789'],
#     "SMTTermsandConditions":"Y"
#     }

# print(json.dumps(params))

url = "https://ors-svc.aws.cloud.oncor.com/customerOutage/outage/checkStatus?esiid=0008973828&source=ORS"

response = requests.get(url)
print(response.json())
print(response.status_code)