import serial
import argparse
import dash
from dash import dcc, html
import plotly.graph_objs as go
from collections import deque

# --- Command line arguments ---
parser = argparse.ArgumentParser()
parser.add_argument("--port", required=True, help="Serial port (e.g. COM3, /dev/ttyUSB0)")
args = parser.parse_args()

# --- Serial setup ---
ser = serial.Serial(args.port, 115200, timeout=1)

# --- Data buffers ---
max_len = 200
time_vals = deque(maxlen=max_len)
temp_vals = deque(maxlen=max_len)
rh_vals = deque(maxlen=max_len)
ah_vals = deque(maxlen=max_len)
heater_vals = deque(maxlen=max_len)

# --- Dash app ---
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Ventilator Monitor Dashboard"),
    dcc.Graph(id="temp-graph"),
    dcc.Graph(id="rh-graph"),
    dcc.Graph(id="ah-graph"),
    html.Div(id="heater-status", style={"fontSize": "24px", "marginTop": "20px"}),
    dcc.Interval(id="interval", interval=500, n_intervals=0)
])

@app.callback(
    [dash.dependencies.Output("temp-graph", "figure"),
     dash.dependencies.Output("rh-graph", "figure"),
     dash.dependencies.Output("ah-graph", "figure"),
     dash.dependencies.Output("heater-status", "children")],
    [dash.dependencies.Input("interval", "n_intervals")]
)
def update_graphs(n):
    try:
        line = ser.readline().decode().strip()
        if line and not line.startswith("time_ms"):
            parts = line.split(",")
            if len(parts) >= 5:
                time_vals.append(int(parts[0]))
                temp_vals.append(float(parts[1]))
                rh_vals.append(float(parts[2]))
                ah_vals.append(float(parts[3]))
                heater_vals.append(int(parts[4]))
    except Exception:
        pass

    temp_fig = go.Figure()
    temp_fig.add_trace(go.Scatter(x=list(time_vals), y=list(temp_vals),
                                  mode="lines+markers", name="Temperature"))
    temp_fig.update_layout(xaxis_title="Time (ms)", yaxis_title="Temperature (°C)")

    rh_fig = go.Figure()
    rh_fig.add_trace(go.Scatter(x=list(time_vals), y=list(rh_vals),
                                mode="lines+markers", name="Relative Humidity"))
    rh_fig.update_layout(xaxis_title="Time (ms)", yaxis_title="RH (%)")

    ah_fig = go.Figure()
    ah_fig.add_trace(go.Scatter(x=list(time_vals), y=list(ah_vals),
                                mode="lines+markers", name="Absolute Humidity"))
    ah_fig.update_layout(xaxis_title="Time (ms)", yaxis_title="AH (g/m³)")

    heater_status = "Heater: ON" if heater_vals and heater_vals[-1] == 1 else "Heater: OFF"

    return temp_fig, rh_fig, ah_fig, heater_status

if __name__ == "__main__":
    app.run_server(debug=True)
