from snmp_library_v2 import *  
import asyncio  
import time  

# Configuración
community = "public"  # Comunidad SNMP
agent_ip = "192.168.153.1"  # Dirección IP del agente SNMP
port = 161  
version = 2  # SNMPv2c
base_oid = '1.3.6.1.2.1.2'  # OID base


async def snmp_walk(snmp_engine, base_oid):
    # OID base para comenzar el recorrido
    varBinds = [ObjectType(ObjectIdentity(base_oid))]

    # Realiza peticiones SNMP hasta que se terminen los resultados
    while True:
        # Solicitud SNMP para obtener el siguiente valor en la tabla
        response = await snmp_engine.next(varBinds)

        # Maneja posibles errores en la respuesta SNMP
        if response.errorIndication:
            print("Error:", response.errorIndication)  # Muestra si hay un error de conexión
            break
        elif response.errorStatus:
            print("Error Status:", response.errorStatus.prettyPrint())  # Muestra errores de SNMP
            break
        else:

            # Verifica si el OID ha cambiado; si ya no pertenece al base_oid, se detiene el recorrido
            for varBind in response.varBinds:
                # Actualiza el OID para la próxima solicitud
                varBinds[0] = ObjectType(ObjectIdentity(varBind[0]))
                if str(varBind[0]).find(base_oid) == -1:  # Verifica si el OID aún está en la tabla
                    return  
                
            # Imprime cada respuesta en la consola inmediatamente
            response.pretty_print()




async def main():
    # Inicializa el motor SNMP 
    snmp_engine = snmp_requests(community, agent_ip, port, version)

    t_start = time.time()  # Guarda el tiempo de inicio
    await snmp_walk(snmp_engine, base_oid)  # Llama a la función walk

    # Calcula y muestra el tiempo total de ejecución
    elapsed_time = time.time() - t_start
    print(f'Tiempo total: {elapsed_time:.2f} segundos')


if __name__ == "__main__":
    asyncio.run(main())  
