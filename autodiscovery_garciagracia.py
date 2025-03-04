import asyncio  
from scapy.all import ARP, Ether, ICMP, IP, srp  
from snmp_library_v2 import snmp_requests, ObjectType, ObjectIdentity  

# Configuración
community = "public"  # Comunidad SNMP 
port = 161  
version = 2  # SNMPv2c
base_oid = '1.3.6.1.2.1.1.1.0'  # OID para "sysDescr"

# Función para escanear la red utilizando ARP
def arp_scan(network_range):
    print(f"Escaneando la red {network_range} utilizando ARP...")

    # Construye el paquete ARP con dirección MAC de difusión para pedir información a todos los dispositivos
    arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_range)

    # Envia el paquete y recibe las respuestas (answered son las respuestas de los dispositivos activos)
    answered, _ = srp(arp_request, timeout=2, verbose=False)
    
    devices = []  # Lista para almacenar IPs de los dispositivos activos
    for _, received in answered:
        devices.append(received.psrc)  # Guarda la IP de cada dispositivo activo
        print(f"Dispositivo activo (ARP): {received.psrc} - MAC: {received.hwsrc}")  # Muestra IP y MAC
    
    return devices  # Devuelve la lista de dispositivos activos

# Función para verificar si un dispositivo soporta SNMP
async def check_snmp(ip):
    snmp_engine = snmp_requests(community, ip, port, version)
    varBinds = [ObjectType(ObjectIdentity(base_oid))]  # Define el OID que se va a consultar
    
    try:
        # Realiza una solicitud SNMP get para obtener información del dispositivo
        response = await snmp_engine.get(varBinds)
        
        # Comprueba si hay errores en la solicitud SNMP
        if response.errorIndication or response.errorStatus:
            return False  # Si hay errores, no soporta SNMP
        else:
            return True  # No hubo errores, el dispositivo soporta SNMP
    except Exception as e:
        return False  # Maneja cualquier otra excepción retornando False

def main():

    # Solicita el rango de IPs al usuario
    network_range = input("Introduce el rango de IPs a escanear (ejemplo: 192.168.153.0/24): ")

    # Escanea la red para identificar dispositivos activos
    active_devices = arp_scan(network_range)

    print("\nVerificando dispositivos que soportan SNMP...")
    for device in set(active_devices):  # Utiliza `set` para evitar IPs duplicadas
        # Ejecuta la función asíncrona `check_snmp` y verifica si el dispositivo soporta SNMP
        if asyncio.run(check_snmp(device)):
            print(f"Dispositivos que soportan SNMP: {device}")

if __name__ == "__main__":
    main()
