import snmp as snmp
from dotenv import load_dotenv
import os

load_dotenv()

community = os.environ['COMMUNITY']

def controller_ping(ip):
    with snmp.Engine(defaultVersion=snmp.SNMPv1,defaultCommunity=community.encode()) as engine:
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