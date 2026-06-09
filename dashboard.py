import serial
import csv
import dash
from dash import dcc, html
import plotly.graph_objs as go
from collections import deque
import threading
import time

# --- Serial Setup ---
PORT = "COM5"   # change to your ESP32-C3 port
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=1)

# --- Data Buffers ---
maxlen = 100
time_data = deque(maxlen=maxlen)
temp_data = deque(maxlen=maxlen)
rh_data = deque(maxlen=maxlen)
ah_data = deque(maxlen=maxlen)

# --- Background Reader Thread ---
def read_serial():
    reader = csv.reader(ser)
    start = time.time()
    for row in reader:
        try:
            # Expecting: time_ms,temperature,relative_humidity,absolute_humidity,heater_state
            if len(row) >= 5 and row[1] != "NaN":
                t_ms = int(row[0])
                temp = float(row[1])
                rh   = float(row[2])
                ah   = float(row[3])

                time_data.append((time.time() - start))
                temp_data.append(temp)
                rh_data.append(rh)
                ah_data.append(ah)
        except Exception:
            continue

threading.Thread(target=read_serial, daemon=True).start()

# --- Dash App ---
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Ventilator Monitor Dashboard"),
    dcc.Interval(id="interval", interval=1000, n_intervals=0),
    dcc.Graph(id="temp-graph"),
    dcc.Graph(id="rh-graph"),
    dcc.Graph(id="ah-graph")
])

@app.callback(
    [dash.Output("temp-graph", "figure"),
     dash.Output("rh-graph", "figure"),
     dash.Output("ah-graph", "figure")],
    [dash.Input("interval", "n_intervals")]
)
def update_graphs(_):
    fig_temp = go.Figure(go.Scatter(x=list(time_data), y=list(temp_data), mode="lines", name="Temp (°C)"))
    fig_temp.update_layout(title="Temperature", xaxis_title="Time (s)", yaxis_title="°C")

    fig_rh = go.Figure(go.Scatter(x=list(time_data), y=list(rh_data), mode="lines", name="RH (%)"))
    fig_rh.update_layout(title="Relative Humidity", xaxis_title="Time (s)", yaxis_title="%")

    fig_ah = go.Figure(go.Scatter(x=list(time_data), y=list(ah_data), mode="lines", name="AH (g/m³)"))
    fig_ah.update_layout(title="Absolute Humidity", xaxis_title="Time (s)", yaxis_title="g/m³")

    return fig_temp, fig_rh, fig_ah

if __name__ == "__main__":
    app.run_server(debug=True)
