# Imports
from snmp_library_v2 import *  
import asyncio
from pysnmp.hlapi.v3arch.asyncio import *
import re
import time

# Parámetros de configuración SNMP
community = "public"
agent_ip = "192.168.153.1" 
port = 161
version = 2  # Usa 1 o 2 según tu configuración

# OIDs del grupo System (ejemplo)
SYSTEM_OIDS = [
    '1.3.6.1.2.1.1.1.0',  # sysDescr
    '1.3.6.1.2.1.1.2.0',  # sysObjectID
    '1.3.6.1.2.1.1.3.0',  # sysUpTime
    '1.3.6.1.2.1.1.4.0',  # sysContact
    '1.3.6.1.2.1.1.5.0',  # sysName
    '1.3.6.1.2.1.1.6.0',  # sysLocation
    '1.3.6.1.2.1.1.7.0'   # sysServices
]

# Inicialización del motor SNMP
snmp_engine = snmp_requests(community, agent_ip, port, version)

# Parte 1: SNMP GET individual para cada objeto
start_time = time.time()
print("=== Parte 1: SNMP GET individual para cada objeto ===")

for oid in SYSTEM_OIDS:
    varBinds = [ObjectType(ObjectIdentity(oid))]
    r = asyncio.run(snmp_engine.get(varBinds))
    r.pretty_print()

end_time = time.time()
print(f"Tiempo total (individual requests): {end_time - start_time:.2f} segundos\n")

# Parte 2: SNMP GET para todos los objetos en una sola solicitud
start_time = time.time()
print("=== Parte 2: SNMP GET para todos los objetos ===")

varBinds = [ObjectType(ObjectIdentity(oid)) for oid in SYSTEM_OIDS]
r = asyncio.run(snmp_engine.get(varBinds))
r.pretty_print()

end_time = time.time()
print(f"Tiempo total (bulk request): {end_time - start_time:.2f} segundos")