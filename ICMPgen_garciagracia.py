from scapy.all import ICMP, IP, sr1
import time

# Configuración
target_ip = "155.210.157.12"  # Dirección IP de destino

def send_icmp_requests(target_ip, n):
    print(f"Enviando {n} paquetes ICMP a {target_ip}...")
    start_time = time.time()  # Inicia el temporizador
    
    for i in range(n):
        packet = IP(dst=target_ip) / ICMP()  # Crea el paquete ICMP
        response = sr1(packet, verbose=False)  # Envía el paquete y espera respuesta
        
        if response:
            print(f"Paquete {i + 1}: Respuesta recibida de {target_ip}")
        else:
            print(f"Paquete {i + 1}: No se recibió respuesta de {target_ip}")
    
    end_time = time.time()  # Detiene el temporizador
    elapsed_time = end_time - start_time  # Calcula el tiempo total
    print(f"\nTiempo total para enviar {n} paquetes: {elapsed_time:.2f} segundos")

def start_icmp_generation(n=20):
    send_icmp_requests(target_ip, n)  # Llama a la función para enviar ICMP

if __name__ == "__main__":
    n = 20  # Número de paquetes ICMP a enviar
    start_icmp_generation(n)  # Llama a la función de inicio si se ejecuta directamente
