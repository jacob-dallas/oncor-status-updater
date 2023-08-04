import snmp as snmp
from dotenv import load_dotenv
import os

data_root = os.path.join(os.getenv('APPDATA'),'acid')
env_path = os.path.join(data_root,'.env')
load_dotenv(env_path)

community = os.environ['COMMUNITY']
versions = {
    '1':snmp.SNMPv1,
    '2':snmp.SNMPv2c,
    '3':snmp.SNMPv3,
}
version = os.environ['SNMPVER']
def controller_ping(ip):
    with snmp.Engine(defaultVersion=versions[version],defaultCommunity=community.encode()) as engine:
        try:
            localhost = engine.Manager((ip,161))
            res = localhost.get("1.3.6.1.4.1.1206.4.2.1.3.8")
            # 128 is coordactive
            # 32 is local flash
            # 48 is local flash and mmu flash
            # 160 is local flash and coord
            # local flash is controller sets flash but is not commanded by mmu or system
            #  
        except snmp.manager.Timeout as error:
            res = False
        return res
    
if __name__ =="__main__":
    print(controller_ping('172.22.4.110'))