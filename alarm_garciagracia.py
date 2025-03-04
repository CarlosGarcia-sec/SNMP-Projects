import asyncio
from snmp_library_v2 import snmp_requests, ObjectType, ObjectIdentity
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scapy.all import sniff, IP, ICMP
from datetime import datetime

# Configuración de correos
EMAIL_SENDER = "snmp.846499@gmail.com"  # Dirección de correo del remitente
EMAIL_PASSWORD = "ssih qrou lcaw kygk"  # Contraseña del correo del remitente
EMAIL_RECEIVER = "garciagraciac8@gmail.com"  # Dirección de correo del destinatario

# Configuración del agente SNMP
agent_ip = "155.210.157.12"  # IP del agente SNMP a monitorizar
community = "public"  # Comunidad SNMP de solo lectura
port = 161  # Puerto SNMP
version = 2  # Versión del protocolo SNMP (SNMPv2c)
oid_icmp_packets = "1.3.6.1.2.1.5.8.0"  # OID para el número de paquetes ICMP recibidos

# Variable global para almacenar la IP de la máquina que envía los paquetes ICMP
icmp_source_ip = None

# Función para enviar alertas por correo electrónico en formato HTML
def send_email_alert(message, icmp_diff, alert_time, attacker_ip):
    # Crear el mensaje con el formato adecuado
    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = '🚨 Alerta de Paquetes ICMP Recibidos 🚨'
    
    # Contenido en HTML
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #d9534f;">⚠️ Alerta ICMP</h2>
        <p><strong>Se ha detectado un exceso de paquetes ICMP en el agente {agent_ip}</strong></p>
        <p><strong>Hora de la alerta:</strong> {alert_time}</p>
        <p><strong>Paquetes ICMP detectados en los últimos 10 segundos:</strong> {icmp_diff}</p>
        <p style="color: #0275d8;"><strong>IP del agente:</strong> {agent_ip}</p>
        <p style="color: #5bc0de;"><strong>IP de la máquina atacante (quien manda los ICMP):</strong> {attacker_ip}</p>
        <p><em>{message}</em></p>
        <p style="color: #5cb85c;">Este es un correo de alerta automática. No responda a este mensaje.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html'))  # Adjuntar el contenido HTML al mensaje
    
    # Conectar con el servidor SMTP y enviar el correo
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Iniciar conexión segura
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)  # Iniciar sesión en el servidor de correo
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)  # Enviar el mensaje
        server.quit()  # Cerrar conexión con el servidor
        print(f"Correo enviado a {EMAIL_RECEIVER}")
    except Exception as e:
        print(f"No se pudo enviar el correo: {str(e)}")

# Función para obtener el número actual de paquetes ICMP recibidos desde el agente SNMP
async def get_icmp_count(snmp_engine):
    try:
        # Realizar una consulta SNMP para obtener el valor de paquetes ICMP
        response = await snmp_engine.get([ObjectType(ObjectIdentity(oid_icmp_packets))])
        if response.errorIndication or response.errorStatus:
            print("Error en la consulta SNMP")
            return 0
        else:
            return int(response.varBinds[0][1])  # Retornar el valor de paquetes ICMP recibidos
    except Exception as e:
        print(f"Se produjo un error en la consulta SNMP: {str(e)}")
        return 0

# Función para monitorizar los paquetes ICMP recibidos en intervalos de 10 segundos
async def check_icmp_count(snmp_engine):
    # Leer el valor inicial de paquetes ICMP
    initial_icmp_count = await get_icmp_count(snmp_engine)
    print(f"Paquetes ICMP iniciales: {initial_icmp_count}")
    
    # Bucle de monitorización en intervalos de 10 segundos
    while True:
        await asyncio.sleep(10)  # Esperar 10 segundos
        current_icmp_count = await get_icmp_count(snmp_engine)
        
        # Calcular la diferencia de paquetes ICMP detectados
        icmp_diff = current_icmp_count - initial_icmp_count
        print(f"Diferencia de paquetes ICMP en los últimos 10 segundos: {icmp_diff}")
        
        # Verificar si el número de paquetes supera el umbral (5 en este caso)
        if icmp_diff > 5:
            print(f"Alerta: Se han detectado {icmp_diff} paquetes ICMP en 10 segundos")
            alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Registrar la hora de la alerta
            send_email_alert(f"{icmp_diff} paquetes ICMP detectados.", icmp_diff, alert_time, icmp_source_ip)
        
        # Actualizar el contador inicial para la siguiente iteración
        initial_icmp_count = current_icmp_count

# Función para capturar la IP de origen de los paquetes ICMP y almacenarla
def capture_icmp_source(packet):
    global icmp_source_ip
    # Verificar si el paquete es ICMP y está dirigido al agente
    if packet.haslayer(ICMP) and packet[IP].dst == agent_ip:
        icmp_source_ip = packet[IP].src  # Guardar la IP del remitente

# Monitorizar el tráfico ICMP en la red y detectar la IP de origen
def monitor_icmp_traffic():
    sniff(filter=f"icmp and dst host {agent_ip}", prn=capture_icmp_source, store=0)

# Función principal
def main():
    snmp_engine = snmp_requests(community, agent_ip, port, version)  # Crear una instancia del motor SNMP
    
    # Iniciar la monitorización de tráfico ICMP en un hilo separado
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, monitor_icmp_traffic)
    
    # Iniciar la monitorización de los paquetes ICMP recibidos por SNMP
    asyncio.run(check_icmp_count(snmp_engine))

# Iniciar el programa
if __name__ == "__main__":
    main()
