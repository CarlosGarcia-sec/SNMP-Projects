import asyncio
from pysnmp.hlapi.asyncio import *


async def snmp_get_v3(agent_ip, port, user, auth_key, priv_key, oid):
    # Datos del usuario para la autenticación y privacidad en SNMPv3
    user_data = UsmUserData(
        user,                     # Nombre de usuario
        authKey=auth_key,         # Clave de autenticación 
        privKey=priv_key,         # Clave de privacidad para el cifrado
        authProtocol=usmHMACSHAAuthProtocol,  # Protocolo de autenticación HMAC-SHA1
        privProtocol=usmAesCfb128Protocol     # Protocolo de privacidad AES con cifrado de 128 bits
    )

    # Creamos un objeto de transporte UDP  que define la IP y el puerto del agente SNMP
    transport = await UdpTransportTarget.create((agent_ip, port))

    # Creamos el contexto de datos para la sesión SNMP
    context = ContextData()

    # Ejecuta la consulta SNMPv3 GET al OID especificado usando el comando getCmd()
    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        SnmpEngine(),             # Motor SNMP 
        user_data,                # Datos del usuario para SNMPv3
        transport,                # Objeto de transporte UDP
        context,                  # Contexto de datos
        ObjectType(ObjectIdentity(oid))  # OID que se va a consultar
    )

    # Procesar la respuesta de la consulta SNMP
    if errorIndication:
        # Si hay un error de comunicación o configuración, se muestra un mensaje de error
        print(f'Error: {errorIndication}')
    elif errorStatus:
        # Si se devuelve un error específico de SNMP, se muestra junto al índice del error
        print(f'Error: {errorStatus.prettyPrint()} at {errorIndex}')
    else:
        # Si la consulta fue exitosa, se muestra el par OID-valor de la respuesta
        for varBind in varBinds:
            print(f'{varBind[0]} = {varBind[1]}')

async def main():
    # Parámetros SNMPv3 del agente
    agent_ip = '192.168.153.1'    # IP del dispositivo 
    port = 161                    # Puerto SNMP 
    user = 'snmpv3mik'            # Usuario SNMPv3
    auth_key = 'contrasenyaSHA1'  # Clave de autenticación HMAC-SHA1
    priv_key = 'contrasenyaAES'   # Clave de privacidad AES-128
    oid = '1.3.6.1.2.1.1.3.0'     # OID del tiempo de actividad del sistema (sysUpTime)

    # Llamada a la función de consulta SNMPv3
    await snmp_get_v3(agent_ip, port, user, auth_key, priv_key, oid)

if __name__ == "__main__":
    asyncio.run(main()) 
