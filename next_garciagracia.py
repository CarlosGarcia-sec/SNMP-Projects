# Imports
from snmp_library_v2 import *
import asyncio
import time

# Función principal
async def main():
    t = time.time()  # Iniciar contador de tiempo

    # Configuración SNMP
    community = "public"  # Cambia esto según tu comunidad SNMP
    agent_ip = "192.168.153.1"  # Cambia esto a la dirección IP de tu agente SNMP
    port = 161
    version = 2

    # OIDs del grupo System, reordenando para que el deseado esté primero
    system_oids = [
        '1.3.6.1.2.1.1.0',    # sysDescr
        '1.3.6.1.2.1.1.1.0',  # sysObjectID
        '1.3.6.1.2.1.1.2.0',  # sysUpTime
        '1.3.6.1.2.1.1.3.0',  # sysContact
        '1.3.6.1.2.1.1.4.0',  # sysName
        '1.3.6.1.2.1.1.5.0',  # sysLocation
        '1.3.6.1.2.1.1.6.0'   # sysServices
    ]

    snmp_engine = snmp_requests(community, agent_ip, port, version)

    # Almacenar respuestas en el orden de los OIDs
    responses = []

    # Parte 1: SNMP GETNEXT individual para cada objeto
    for oid in system_oids:
        varBinds = [ObjectType(ObjectIdentity(oid))]
        response = await snmp_engine.next(varBinds)
        responses.append(response)

    # Imprimir las respuestas en el orden de los OIDs
    for response in responses:
        response.pretty_print()

    # Tiempo total
    elapsed = time.time() - t
    print('Tiempo total (individual requests): ' + str(elapsed) + ' segundos')

# Ejecutar la función principal
if __name__ == "__main__":
    asyncio.run(main())
