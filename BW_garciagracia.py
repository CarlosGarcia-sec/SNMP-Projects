import asyncio
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from snmp_library_v2 import snmp_requests
from datetime import datetime, timedelta
from pysnmp.hlapi.v3arch.asyncio import *

# Configuración del dispositivo SNMP
agent_ip = None
community = None
version = None


if agent_ip is None or community is None or version is None:
    agent_ip = input("Escoge la IP del agente SNMP:")
    community = input("Escoge la comunidad del agente SNMP:")
    port = 161
    version = input("Escoge la version (1 o 2):")

# OIDs necesarios
OID_IFNAME = '1.3.6.1.2.1.2.2.1.2'  # OID de nombres de interfaz
OID_IN_OCTETS = '1.3.6.1.2.1.2.2.1.10'  # OID base para octetos de entrada
OID_OUT_OCTETS = '1.3.6.1.2.1.2.2.1.16'  # OID base para octetos de salida

# Inicializamos la instancia para solicitudes SNMP
snmp_client = snmp_requests(community, agent_ip, port, version)

# Lista para almacenar interfaces detectadas
interfaces = []

# Variables para almacenamiento de datos históricos
timestamps = []
upload_rates = []
download_rates = []

# Variables para contadores de octetos anteriores
previous_in_octets = None
previous_out_octets = None
previous_time = None

# Variable global para la interfaz seleccionada previamente
selected_interface = None

# Función para obtener la lista de interfaces disponibles
async def get_interfaces(snmp_req):
    interfaces = {}
    next_oid = OID_IFNAME
    
    while True:
        response = await snmp_req.next([ObjectType(ObjectIdentity(next_oid))])
        if response.errorIndication or response.errorStatus:
            print("Error en la consulta SNMP:", response.errorIndication or response.errorStatus.prettyPrint())
            break
        
        for varBind in response.varBinds:
            oid_str = str(varBind[0])
            if not oid_str.startswith(OID_IFNAME):
                return interfaces
            
            interface_index = oid_str.split('.')[-1]
            interfaces[interface_index] = str(varBind[1])
            next_oid = oid_str
    return interfaces

# Función para obtener tasas de subida y bajada en bps
async def get_bandwidth(snmp_req, interface_index):
    global previous_in_octets, previous_out_octets, previous_time
    
    in_oid = OID_IN_OCTETS + '.' + interface_index
    out_oid = OID_OUT_OCTETS + '.' + interface_index
    
    response_in = await snmp_req.get([ObjectType(ObjectIdentity(in_oid))])
    response_out = await snmp_req.get([ObjectType(ObjectIdentity(out_oid))])
    
    current_in_octets = int(response_in.varBinds[0][1])
    current_out_octets = int(response_out.varBinds[0][1])
    current_time = datetime.now()
    
    # Si es la primera medición, inicializar los valores anteriores
    if previous_in_octets is None or previous_out_octets is None:
        previous_in_octets = current_in_octets
        previous_out_octets = current_out_octets
        previous_time = current_time
        return 0, 0
    
    # Calcular la diferencia en octetos y tiempo
    time_diff = (current_time - previous_time).total_seconds()
    in_octets_diff = current_in_octets - previous_in_octets
    out_octets_diff = current_out_octets - previous_out_octets
    
    # Actualizar valores anteriores para la próxima iteración
    previous_in_octets = current_in_octets
    previous_out_octets = current_out_octets
    previous_time = current_time
    
    # Convertir la diferencia de octetos a bps
    upload_rate = (out_octets_diff * 8) / time_diff if time_diff > 0 else 0
    download_rate = (in_octets_diff * 8) / time_diff if time_diff > 0 else 0
    
    return upload_rate, download_rate

# Configuración de la aplicación Dash
app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#f4f4f4', 'padding': '20px'}, children=[
    html.H1("Monitorización de Ancho de Banda en Tiempo Real", style={'textAlign': 'center', 'color': '#333'}),
    
    html.Label("Selecciona la interfaz:"),
    dcc.Dropdown(id='interface-dropdown', options=[], placeholder="Selecciona una interfaz..."),

    html.Div(dcc.Graph(id='bandwidth-graph'), style={'width': '100%'}),

    dcc.Interval(
        id='interval-component',
        interval=2 * 1000,
        n_intervals=0
    )
])

# Callback para actualizar las opciones del dropdown de interfaz
@app.callback(
    Output('interface-dropdown', 'options'),
    Input('interval-component', 'n_intervals')
)
def update_interfaces_dropdown(n):
    global interfaces
    interfaces_dict = asyncio.run(get_interfaces(snmp_client))
    interfaces = [(index, name) for index, name in interfaces_dict.items()]
    return [{'label': name, 'value': index} for index, name in interfaces]

# Callback para actualizar la gráfica
@app.callback(
    Output('bandwidth-graph', 'figure'),
    [Input('interface-dropdown', 'value'), Input('interval-component', 'n_intervals')]
)
def update_graph(interface_index, n):
    global selected_interface, timestamps, upload_rates, download_rates

    # Reinicio de datos si cambia la interfaz
    if interface_index != selected_interface:
        selected_interface = interface_index
        timestamps = []
        upload_rates = []
        download_rates = []

    if interface_index is None:
        return go.Figure()

    # Obtener los datos de ancho de banda
    try:
        upload_rate, download_rate = asyncio.run(get_bandwidth(snmp_client, interface_index))
        timestamp = datetime.now()
        
        # Actualizar datos históricos
        timestamps.append(timestamp)
        upload_rates.append(upload_rate)
        download_rates.append(download_rate)

        # Limitar el historial a 60 segundos
        current_time = datetime.now()
        time_limit = current_time - timedelta(seconds=60)
        
        # Filtrar datos para la visualización
        filtered_timestamps = [t for t in timestamps if t >= time_limit]
        filtered_upload_rates = [rate for rate, t in zip(upload_rates, timestamps) if t >= time_limit]
        filtered_download_rates = [rate for rate, t in zip(download_rates, timestamps) if t >= time_limit]

        # Crear la gráfica de áreas
        fig = go.Figure()

        # Tasa de subida con área rellena y hacia abajo
        fig.add_trace(go.Scatter(
            x=filtered_timestamps,
            y=[-rate for rate in filtered_upload_rates],  # Invertimos la tasa de subida para mostrarla hacia abajo
            mode='lines',
            fill='tozeroy',
            line=dict(color='red', shape='spline'),  # Suavizamos la línea con 'shape=spline'
            name='Tasa de Subida'
        ))

        # Tasa de bajada con área rellena y hacia arriba
        fig.add_trace(go.Scatter(
            x=filtered_timestamps,
            y=filtered_download_rates,
            mode='lines',
            fill='tozeroy',
            line=dict(color='blue', shape='spline'),  # Suavizamos la línea con 'shape=spline'
            name='Tasa de Bajada'
        ))


        fig.update_layout(
            title=f'Monitorización de Ancho de Banda para Interfaz {interface_index}',
            xaxis_title='Tiempo',
            yaxis_title='Tasa (bps)',
            xaxis=dict(range=[time_limit, current_time]),
            yaxis=dict(range=[-max(max(filtered_upload_rates, default=0), max(filtered_download_rates, default=0)) - 1000, 
                              max(max(filtered_download_rates, default=0), max(filtered_upload_rates, default=0)) + 1000]),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(255,255,255,0.95)',
            font=dict(color='#333')
        )
    except Exception as e:
        print(f"Error obteniendo los datos: {e}")
        return go.Figure()

    return fig

if __name__ == '__main__':
    
    app.run_server(debug=True)
