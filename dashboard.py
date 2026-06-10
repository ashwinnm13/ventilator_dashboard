import serial
import threading
from collections import deque
from dash import Dash, dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go

# -----------------------------
# Serial Port Settings
# -----------------------------
PORT = "COM9"      # Change if needed
BAUD = 115200

ser = None

# -----------------------------
# Data Buffers
# -----------------------------
max_len = 200

time_data = deque(maxlen=max_len)
temp_data = deque(maxlen=max_len)
hum_data = deque(maxlen=max_len)
abs_data = deque(maxlen=max_len)
heater_data = deque(maxlen=max_len)

# -----------------------------
# Background Serial Reader
# -----------------------------
def read_serial():
    global ser

    while True:
        try:
            if ser is None or not ser.is_open:
                continue

            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if "," not in line:
                continue

            parts = line.split(",")

            if len(parts) != 5:
                continue

            t_ms = int(parts[0])
            temp = float(parts[1])
            hum = float(parts[2])
            abs_h = float(parts[3])
            heater = int(parts[4])

            time_data.append(t_ms)
            temp_data.append(temp)
            hum_data.append(hum)
            abs_data.append(abs_h)
            heater_data.append(heater)

        except Exception as e:
            print("Serial Read Error:", e)

# -----------------------------
# Dash App
# -----------------------------
app = Dash(__name__)

def heater_color(state):
    return "green" if state == 1 else "red"

app.layout = html.Div([
    html.H1("Ventilator Dashboard — Live Sensor Data"),

    html.Div(
        id="heater-indicator",
        style={
            "width": "220px",
            "height": "60px",
            "fontSize": "28px",
            "fontWeight": "bold",
            "color": "white",
            "textAlign": "center",
            "lineHeight": "60px",
            "borderRadius": "10px",
            "marginBottom": "20px",
        }
    ),

    dcc.Graph(id="temp-graph"),
    dcc.Graph(id="hum-graph"),
    dcc.Graph(id="abs-graph"),
    dcc.Graph(id="heater-graph"),

    dcc.Interval(
        id="interval",
        interval=1000,
        n_intervals=0
    )
])

@app.callback(
    [
        Output("heater-indicator", "children"),
        Output("heater-indicator", "style"),
        Output("temp-graph", "figure"),
        Output("hum-graph", "figure"),
        Output("abs-graph", "figure"),
        Output("heater-graph", "figure"),
    ],
    [Input("interval", "n_intervals")]
)
def update_graph(_):

    heater_state = heater_data[-1] if heater_data else 0

    indicator_style = {
        "width": "220px",
        "height": "60px",
        "fontSize": "28px",
        "fontWeight": "bold",
        "color": "white",
        "textAlign": "center",
        "lineHeight": "60px",
        "borderRadius": "10px",
        "marginBottom": "20px",
        "backgroundColor": heater_color(heater_state),
    }

    fig_temp = go.Figure(
        data=[go.Scatter(
            x=list(time_data),
            y=list(temp_data),
            mode="lines"
        )]
    )
    fig_temp.update_layout(title="Temperature (°C)")

    fig_hum = go.Figure(
        data=[go.Scatter(
            x=list(time_data),
            y=list(hum_data),
            mode="lines"
        )]
    )
    fig_hum.update_layout(title="Relative Humidity (%)")

    fig_abs = go.Figure(
        data=[go.Scatter(
            x=list(time_data),
            y=list(abs_data),
            mode="lines"
        )]
    )
    fig_abs.update_layout(title="Absolute Humidity (g/m³)")

    fig_heater = go.Figure(
        data=[go.Scatter(
            x=list(time_data),
            y=list(heater_data),
            mode="lines"
        )]
    )
    fig_heater.update_layout(title="Heater State (1 = ON, 0 = OFF)")

    return (
        "HEATER ON" if heater_state else "HEATER OFF",
        indicator_style,
        fig_temp,
        fig_hum,
        fig_abs,
        fig_heater
    )

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    try:
        print(f"Opening serial port {PORT}...")

        ser = serial.Serial(PORT, BAUD, timeout=1)

        print("Serial port opened successfully.")

        threading.Thread(
            target=read_serial,
            daemon=True
        ).start()

        app.run(
            debug=True,
            use_reloader=False
        )

    except Exception as e:
        print("Failed to open serial port:")
        print(e)