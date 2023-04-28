import snmp as snmp

with snmp.Engine(defaultVersion=snmp.SNMPv1,defaultCommunity=b'C0DTRN') as engine:
    
    localhost = engine.Manager(('172.22.4.110',161))
    res = localhost.get("1.3.6.1.2.1.1.4.0")
    print(res)