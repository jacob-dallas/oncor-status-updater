import requests
import json
import urllib3
import datetime

root_url = "https://services8.arcgis.com/Lagc28ejuouC6FL3/arcgis/rest/services/"

class GisInt():
    def __init__(self,root_url):
        self.root_url = root_url
        self.auth_time = datetime.datetime.now()-datetime.timedelta(seconds=10)
        self.token = None

    def gis_auth(self):
        if self.auth_time<datetime.datetime.now():
            url =" https://www.arcgis.com/sharing/rest/oauth2/token/"
            res = requests.post(url, {
                'client_id': "",
                'client_secret': "",
                'grant_type': "client_credentials"
                }).json()
            
            self.auth_time = datetime.datetime.now()+datetime.timedelta(seconds=(res['expires_in']-10))
            self.token = res['access_token']



    def gis_query(self,flayer,layerdef):
        url = self.root_url+f'{flayer}/FeatureServer/query'
        self.gis_auth()
        res = requests.get(
            url,
            params={
                'layerDefs':json.dumps(layerdef),
                'token':self.token,
                'f':'json'
            }
        ).json()

        return res
    
    def update(self,flayer,layer,features):
        url = self.root_url+f'{flayer}/FeatureServer/{layer}/UpdateFeatures'
        self.gis_auth()
        res = requests.post(
            url,
            params={
                'layerDefs':json.dumps(features),
                'token':self.token,
                'f':'json'
            }
        ).json()
        return res
    
    def update(self,flayer,layer,features):
        url = self.root_url+f'{flayer}/FeatureServer/{layer}/addFeatures'
        self.gis_auth()
        res = requests.post(
            url,
            params={
                'layerDefs':json.dumps(features),
                'token':self.token,
                'f':'json'
            }
        ).json()
        return res


features = [
    {
        "attributes":{
                "OBJECTID":2,
                "BLOCKNM":"badness",
        }
    }
]

layerdef = {
    "1":"1=1"
}

gis = GisInt(root_url)
res = gis.gis_query('DAL_TRN_TEST',layerdef)
print(res)
