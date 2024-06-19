import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc
import dash, time
from flask import Flask
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
import openai_conn
import plotly.graph_objects as go

server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "NTT EcoHUB"

# Initial dummy data values
initial_gas = 5
initial_electricity = 3
initial_water = 4

# Function to generate data
def generate_data(initial_value, min_value, max_value, data_label, anomaly=False):
    # Generate date range for 7 days with hourly frequency (24 hours per day * 7 days)
    dates = pd.date_range(start=datetime.now() - timedelta(days=6), periods=7*24, freq='h')
    
    # Generate historical data for the first 4 days (96 hours)
    historical = [initial_value] + [random.uniform(min_value, max_value) for _ in range((4*24) - 2)]
    
    # Insert an anomaly in the historical data if specified
    if anomaly:
        anomaly_value = max_value * random.uniform(2.11, 2.48)  # Making the anomaly value significantly higher
        historical.insert(random.randint(1, 4*24 - 2), anomaly_value)
    else:
        historical.append(random.uniform(min_value, max_value))

    # Generate prediction data for the next 3 days (72 hours), starting from the last historical value
    predictions = [historical[-1]] + [random.uniform(min_value, max_value) for _ in range((3*24) - 1)]
    
    # Combine the historical and prediction data
    combined_data = historical + predictions
    
    # Create a list of types with the same length as the data
    types = ['Historisch'] * (4*24) + ['Vorhersage'] * (3*24)

    return dates, combined_data, types

# Generate data for each resource
dates, gas_data, gas_types = generate_data(initial_gas, 3.0, 7.0, "Gasverbrauch (l/m3)")
_, electricity_data, electricity_types = generate_data(initial_electricity, 2.0, 20.0, "Stromverbrauch (kWh)", anomaly=True)
_, water_data, water_types = generate_data(initial_water, 3.0, 5.0, "Wasserverbrauch (l/m3)")

max_electricity = 0
# Create figures function with units parameter
def create_figure(dates, data, types, title, yaxis_units, highlight_max=False):
    global max_electricity
    df = pd.DataFrame({"Datum": dates, "Verbrauch": data, "Typ": types})
    fig = px.line(df, x="Datum", y="Verbrauch", color='Typ', title=title,
                  color_discrete_map={'Historisch': 'blue', 'Vorhersage': 'red'})  # Map colors
    fig.update_layout(xaxis_title="Datum", yaxis_title=f"Verbrauch ({yaxis_units})")
    
    if highlight_max and 'Historisch' in types:
        max_value = max([val for val, typ in zip(data, types) if typ == 'Historisch'])
        max_index = data.index(max_value)
        max_electricity = [round(max_value, 2), dates[max_index]]
        fig.add_trace(go.Scatter(
            x=[dates[max_index]],
            y=[max_value],
            mode='markers',
            marker=dict(color='red', size=10),
            name='Max Historisch'
        ))

    return fig

# Create figures for each type of consumption with appropriate units
gas_fig = create_figure(dates, gas_data, gas_types, "Gasverbrauch im Zeitverlauf", "m³")
electricity_fig = create_figure(dates, electricity_data, electricity_types, "Stromverbrauch im Zeitverlauf", "kWh", highlight_max=True)
water_fig = create_figure(dates, water_data, water_types, "Wasserverbrauch im Zeitverlauf", "m³")

def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div(html.Img(src="assets/logo-no-background.png", width=200))),
                dbc.Col(
                    html.Div("Business Innovation"),
                    style={"text-align": "center",
                           "margin-right": "3em",
                           "font-weight": "bold",
                           "font-size": "40px",
                           "padding-top": "25px",
                           },
                ),
                dbc.Col(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Start", active=True, href="#")),
                            dbc.NavItem(dbc.NavLink("Scope 1", href="#")),
                            dbc.NavItem(dbc.NavLink("Scope 2", href="#")),
                            dbc.NavItem(dbc.NavLink("Scope 3", href="#")),
                            dbc.NavItem(dbc.NavLink("Export", href="#")),
                            dbc.NavItem(dbc.NavLink("KI", id="open-lg", className="me-1", n_clicks=0, href="#")),
                        ], fill=True, pills=True
                    ),
                    style={"text-align": "center", "padding-top": "2em"}
                ),
            ],
            style={"padding-top": "10px"}
        ),

        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("KI Assistent")),
                dbc.ModalBody([
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col([
                                        html.Div(
                                            [
                                                dbc.Spinner(html.Div(id="loading-output")),
                                            ]
                                        ),
                                        html.P("", id="output", n_clicks=0),
                                        dbc.ListGroup(id="list",
                                            children = [],
                                        ),
                                    ],
                                    ),
                                ],
                                style={"padding-bottom": "10px"},
                                # className="h-75",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Textarea(id="input", placeholder="Frage etwas...", size="sm", n_submit=0),
                                        width=10,
                                    ),
                                    dbc.Col(
                                        dbc.Button("Senden", color="primary", className="me-1", id="submit", n_clicks=0),
                                        width=2,
                                    ),
                                ],
                                # style={"padding-right": "20px", "padding-left": "30em", "padding-bottom": "40px"},
                            ),
                        ],
                    ),
                ]),
            ],
            id="modal-lg",
            size="lg",
            is_open=False,
        ),

        dbc.Row(
            [
                dbc.Col(dbc.Card(
                    [dbc.CardBody(f"Stromverbrauch: {initial_electricity} units", id="output-electricity")], color="info", inverse=True, id="output-electricity-card"),
                    width=4),
                dbc.Col(dbc.Card(
                    [dbc.CardBody(f"Gasverbrauch: {initial_gas} units", id="output-gas")], color="secondary", inverse=True, id="output-gas-card"),
                    width=4),
                dbc.Col(dbc.Card(
                    [dbc.CardBody(f"Wasserverbrauch: {initial_water} units", id="output-water")], color="primary", inverse=True, id="output-water-card"),
                    width=4),
            ],
            style={"margin-top": "20px"}
        ),
        dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0),  # Update every second

        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='graph-electricity', figure=electricity_fig), width=12),
                dbc.Col(dcc.Graph(id='graph-gas', figure=gas_fig), width=12),
                dbc.Col(dcc.Graph(id='graph-water', figure=water_fig), width=12),
            ],
            style={"margin-top": "20px"}
        ),

        dbc.Row(
            [
                html.P("Prototype @ Uni Leipzig | SS 2024")
            ],
            className="fixed-bottom",
            style={"textAlign": "center",
                   "margin-top": "3em"},
        ),
    ],
    style={"margin-right": "1em", "margin-left": "1em"}
)

app.callback(
    Output("modal-lg", "is_open"),
    Input("open-lg", "n_clicks"),
    State("modal-lg", "is_open"),
)(toggle_modal)

# User Input
@app.callback([Output("input", "value"),
               Output("list", "children"),
                Output("output", "children")],
              [Input("submit", "n_clicks"),
               Input("input", "n_submit")],
              [State("input", "value"),
              State("list", "children")],
               prevent_initial_call=True)
def output_text(n_clicks, n_submit, value, list_children):
    if n_clicks > 0 or n_submit > 0:
        if value:
            list_children.append(dbc.ListGroupItem("User: " + value, color="primary"))
            return "", list_children, " "
        else:
            return "", list_children, " "
    else:
        return "", list_children, " "

# Agent response
@app.callback([Output("list", "children", allow_duplicate=True),
               Output("loading-output", "children")],
              [Input("output", "children")],
              [State("list", "children")],
              prevent_initial_call=True)
def agent_update(output_children, list_children):
    global max_electricity
    print(max_electricity)
    openai_response = openai_conn.ask_gpt(list_children[-1]['props']['children'][6:], max_electricity)
    list_children.append(dbc.ListGroupItem("Agent: " + openai_response, color="success"))
    return list_children, ""

prev_gas = initial_gas
prev_electricity = initial_electricity
prev_water = initial_water

@app.callback(
    [Output("interval-component", "n_intervals"),
     Output("output-gas", "children"),
     Output("output-electricity", "children"),
     Output("output-water", "children"),
     Output("output-electricity-card", "color"),
     Output("output-gas-card", "color"),
     Output("output-water-card", "color"),],
    [Input("interval-component", "n_intervals")]
)
def update_metrics(n):
    global prev_gas
    global prev_electricity
    global prev_water

    color_elec = "primary"
    color_gas = "primary"
    color_water = "primary"

    # Berechnung neuer Werte
    # gas = round(min(max(prev_gas + random.uniform(-0.1, 0.1), 3.0), 7.0), 2)
    # electricity = round(min(max(prev_electricity + random.uniform(-0.1, 0.1), 2.0), 10.0), 2)
    # water = round(min(max(prev_water + random.uniform(-0.1, 0.1), 3.0), 5.0), 2)
    gas = round(prev_gas + random.uniform(-0.2, 0.2), 2)
    electricity = round(prev_electricity + random.uniform(-0.2, 0.2), 2)
    water = round(prev_water + random.uniform(-0.2, 0.2), 2)

    # Aktualisierung der vorherigen Werte

    if n % 10 == 0:
        gas = 2.0
        electricity = 13.0
        water = 3.0

    if n % 25 == 0:
        gas = 8.0
        electricity = 6.0
        water = 9.0

    prev_gas = gas
    prev_electricity = electricity
    prev_water = water

    if gas < 3:
        color_gas = "success"
    elif gas < 7:
        color_gas = "warning"
    else:
        color_gas = "danger"

    if electricity < 2:
        color_elec = "success"
    elif electricity < 10:
        color_elec = "warning"
    else:
        color_elec = "danger"

    if water < 3:
        color_water = "success"
    elif water < 5:
        color_water = "warning"
    else:
        color_water = "danger"
    
    return n, f"Aktueller Gasverbrauch: {gas} m\u00B3/h", f"Aktueller Stromverbrauch: {electricity} kWh", f"Aktueller Wasserverbrauch: {water} m\u00B3/h", color_elec, color_gas, color_water

app.run_server(debug=True, host="0.0.0.0", port="8050")