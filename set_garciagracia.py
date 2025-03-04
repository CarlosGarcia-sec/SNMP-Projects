# Imports
from snmp_library_v2 import *
import asyncio
import time

# Función principal
async def main():
    # Configuración SNMP
    community = "torocuervo" 
    agent_ip = "192.168.153.1" 
    port = 161
    version = 2

    # OID del objeto sysLocation
    sys_location_oid = "1.3.6.1.2.1.1.6.0"  # sysLocation

    # Nuevo valor para sysLocation
    new_location = "Laboratorio Seguridad" 

    # Inicializar el objeto snmp_requests
    snmp_engine = snmp_requests(community, agent_ip, port, version)

    # Modificar el valor de sysLocation
    varBinds = [ObjectType(ObjectIdentity(sys_location_oid), OctetString(new_location))]
    response = await snmp_engine.set(varBinds)

    # Mostrar el resultado
    response.pretty_print()

# Ejecutar la función principal
if __name__ == "__main__":
    asyncio.run(main())
