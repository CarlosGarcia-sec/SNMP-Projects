import asyncio
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from snmp_library_v2 import snmp_requests
from datetime import datetime, timedelta

# Configuración del dispositivo SNMP
community = 'public'
agent_ip = '155.210.157.216'
port = 161
version = 2

# Inicializamos la instancia para solicitudes SNMP
snmp_client = snmp_requests(community, agent_ip, port, version)

# OIDs de temperatura y velocidad del ventilador
cpu1_temperature_oid_int = '1.3.6.1.4.1.21317.1.3.1.2.1'
cpu2_temperature_oid_int = '1.3.6.1.4.1.21317.1.3.1.2.2'
temperatura_ambiente_oid = '1.3.6.1.4.1.21317.1.3.1.2.11'
fan1_speed_oid_int = '1.3.6.1.4.1.21317.1.3.1.2.65'
fan2_speed_oid_int = '1.3.6.1.4.1.21317.1.3.1.2.66'

# Variables para almacenar los datos
cpu1_temps = []
cpu2_temps = []
ambient_temps = []
fan1_speeds = []
fan2_speeds = []
timestamps = []

# Función para obtener los datos SNMP
async def fetch_data():
    # Obtener temperatura de la CPU1
    cpu1_temp_response = await snmp_client.get([(cpu1_temperature_oid_int, None)])
    cpu1_temp = int(cpu1_temp_response.varBinds[0][1]) if cpu1_temp_response.varBinds else None

    # Obtener temperatura de la CPU2
    cpu2_temp_response = await snmp_client.get([(cpu2_temperature_oid_int, None)])
    cpu2_temp = int(cpu2_temp_response.varBinds[0][1]) if cpu2_temp_response.varBinds else None

    # Obtener temperatura ambiente
    ambient_temp_response = await snmp_client.get([(temperatura_ambiente_oid, None)])
    ambient_temp = int(ambient_temp_response.varBinds[0][1]) if ambient_temp_response.varBinds else None

    # Obtener velocidad del ventilador 1
    fan1_speed_response = await snmp_client.get([(fan1_speed_oid_int, None)])
    fan1_speed = int(fan1_speed_response.varBinds[0][1]) if fan1_speed_response.varBinds else None

    # Obtener velocidad del ventilador 2
    fan2_speed_response = await snmp_client.get([(fan2_speed_oid_int, None)])
    fan2_speed = int(fan2_speed_response.varBinds[0][1]) if fan2_speed_response.varBinds else None

    # Registrar el tiempo actual
    timestamp = datetime.now()

    return timestamp, cpu1_temp, cpu2_temp, ambient_temp, fan1_speed, fan2_speed

# Configuración de la aplicación Dash
app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#f4f4f4', 'padding': '20px'}, children=[
    html.H1("Monitorización de CPU y Ventilador en Tiempo Real", style={'textAlign': 'center', 'color': '#333'}),

    # Contenedor para las gráficas
    html.Div(
        children=[
            # Gráfica para la temperatura de la CPU1
            html.Div(dcc.Graph(id='cpu1-temp-graph'), style={'width': '48%', 'display': 'inline-block'}),
            # Gráfica para la temperatura de la CPU2
            html.Div(dcc.Graph(id='cpu2-temp-graph'), style={'width': '48%', 'display': 'inline-block'}),
            # Gráfica para la temperatura ambiente
            html.Div(dcc.Graph(id='ambient-temp-graph'), style={'width': '48%', 'display': 'inline-block'}),
            # Gráfica para la velocidad del ventilador 1
            html.Div(dcc.Graph(id='fan1-speed-graph'), style={'width': '48%', 'display': 'inline-block'}),
            # Gráfica para la velocidad del ventilador 2
            html.Div(dcc.Graph(id='fan2-speed-graph'), style={'width': '48%', 'display': 'inline-block'}),
        ],
        style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'space-between'}
    ),

    # Intervalo de actualización
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # Intervalo en milisegundos (5 segundos)
        n_intervals=0
    )
])

@app.callback(
    [Output('cpu1-temp-graph', 'figure'),
     Output('cpu2-temp-graph', 'figure'),
     Output('ambient-temp-graph', 'figure'),
     Output('fan1-speed-graph', 'figure'),
     Output('fan2-speed-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    # Llamar a la función fetch_data y actualizar los datos
    timestamp, cpu1_temp, cpu2_temp, ambient_temp, fan1_speed, fan2_speed = asyncio.run(fetch_data())
  
    # Agregar nuevos datos a las listas
    if cpu1_temp is not None:
        cpu1_temps.append(cpu1_temp)
    if cpu2_temp is not None:
        cpu2_temps.append(cpu2_temp)
    if ambient_temp is not None:
        ambient_temps.append(ambient_temp)
    if fan1_speed is not None:
        fan1_speeds.append(fan1_speed)
    if fan2_speed is not None:
        fan2_speeds.append(fan2_speed)
      
    timestamps.append(timestamp)

    # Limitar el historial a los últimos 60 segundos
    current_time = datetime.now()
    time_limit = current_time - timedelta(seconds=60)

    # Filtrar datos
    cpu1_temps_filtered = [temp for temp, time in zip(cpu1_temps, timestamps) if time >= time_limit]
    cpu2_temps_filtered = [temp for temp, time in zip(cpu2_temps, timestamps) if time >= time_limit]
    ambient_temps_filtered = [temp for temp, time in zip(ambient_temps, timestamps) if time >= time_limit]
    fan1_speeds_filtered = [speed for speed, time in zip(fan1_speeds, timestamps) if time >= time_limit]
    fan2_speeds_filtered = [speed for speed, time in zip(fan2_speeds, timestamps) if time >= time_limit]
    timestamps_filtered = [time for time in timestamps if time >= time_limit]

    # Crear gráfico para la temperatura de la CPU1
    cpu1_temp_fig = go.Figure()
    cpu1_temp_fig.add_trace(go.Scatter(
        x=timestamps_filtered, y=cpu1_temps_filtered, mode='lines', fill='tozeroy', line=dict(color='firebrick'), name='Temperatura CPU1'
    ))
    cpu1_temp_fig.update_layout(
        title='Temperatura CPU1',
        xaxis_title='Tiempo',
        yaxis_title='Temperatura (°C)',
        xaxis=dict(range=[time_limit, current_time]),
        yaxis=dict(range=[min(cpu1_temps_filtered) - 5, max(cpu1_temps_filtered) + 5]),
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
        paper_bgcolor='rgba(255,255,255,0.95)',  # Fondo del gráfico
        font=dict(color='#333')
    )

    # Crear gráfico para la temperatura de la CPU2
    cpu2_temp_fig = go.Figure()
    cpu2_temp_fig.add_trace(go.Scatter(
        x=timestamps_filtered, y=cpu2_temps_filtered, mode='lines', fill='tozeroy', line=dict(color='mediumseagreen'), name='Temperatura CPU2'
    ))
    cpu2_temp_fig.update_layout(
        title='Temperatura CPU2',
        xaxis_title='Tiempo',
        yaxis_title='Temperatura (°C)',
        xaxis=dict(range=[time_limit, current_time]),
        yaxis=dict(range=[min(cpu2_temps_filtered) - 5, max(cpu2_temps_filtered) + 5]),
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(255,255,255,0.95)',
        font=dict(color='#333')
    )

    # Crear gráfico para la temperatura ambiente
    ambient_temp_fig = go.Figure()
    ambient_temp_fig.add_trace(go.Scatter(
        x=timestamps_filtered, y=ambient_temps_filtered, mode='lines', fill='tozeroy', line=dict(color='gold'), name='Temperatura Ambiente'
    ))
    ambient_temp_fig.update_layout(
        title='Temperatura Ambiente',
        xaxis_title='Tiempo',
        yaxis_title='Temperatura (°C)',
        xaxis=dict(range=[time_limit, current_time]),
        yaxis=dict(range=[min(ambient_temps_filtered) - 5, max(ambient_temps_filtered) + 5]),
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(255,255,255,0.95)',
        font=dict(color='#333')
    )

    # Crear gráfico para la velocidad del ventilador 1
    fan1_speed_fig = go.Figure()
    fan1_speed_fig.add_trace(go.Scatter(
        x=timestamps_filtered, y=fan1_speeds_filtered, mode='lines', fill='tozeroy', line=dict(color='deepskyblue'), name='Velocidad Ventilador 1'
    ))
    fan1_speed_fig.update_layout(
        title='Velocidad Ventilador 1',
        xaxis_title='Tiempo',
        yaxis_title='Velocidad (RPM)',
        xaxis=dict(range=[time_limit, current_time]),
        yaxis=dict(range=[min(fan1_speeds_filtered) - 100, max(fan1_speeds_filtered) + 100]),
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(255,255,255,0.95)',
        font=dict(color='#333')
    )

    # Crear gráfico para la velocidad del ventilador 2
    fan2_speed_fig = go.Figure()
    fan2_speed_fig.add_trace(go.Scatter(
        x=timestamps_filtered, y=fan2_speeds_filtered, mode='lines', fill='tozeroy', line=dict(color='orange'), name='Velocidad Ventilador 2'
    ))
    fan2_speed_fig.update_layout(
        title='Velocidad Ventilador 2',
        xaxis_title='Tiempo',
        yaxis_title='Velocidad (RPM)',
        xaxis=dict(range=[time_limit, current_time]),
        yaxis=dict(range=[min(fan2_speeds_filtered) - 100, max(fan2_speeds_filtered) + 100]),
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(255,255,255,0.95)',
        font=dict(color='#333')
    )

    return cpu1_temp_fig, cpu2_temp_fig, ambient_temp_fig, fan1_speed_fig, fan2_speed_fig

if __name__ == '__main__':
    app.run_server(debug=True)
