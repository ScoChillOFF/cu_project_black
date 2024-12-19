import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for
import dash
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output

from app.services.geocoder import Geocoder
from app.services.weather import WeatherService
from app.utils import is_connected
from app.config import config

server = Flask(__name__)

app = dash.Dash(__name__, server=server, url_base_pathname="/dash/")

df = pd.DataFrame()

app.layout = html.Div([
    html.H1("Прогноз погоды", style={"textAlign": "center", "font-family": "Roboto, sans-serif"}),
    html.Label("Выберите город:", style={"color": "#003366", "font-family": "Roboto, sans-serif"}),
    dcc.Dropdown(
        id="city-dropdown",
        options=[],
        value=None,
        style={"width": "50%", "margin": "10px 0", "font-family": "Roboto, sans-serif"}
    ),
    html.Label("Выберите количество дней для прогноза:", style={"color": "#003366", "font-family": "Roboto, sans-serif"}),
    dcc.Dropdown(
        id="days-dropdown",
        options=[
            {"label": "1 день", "value": "1"},
            {"label": "3 дня", "value": "3"},
            {"label": "5 дней", "value": "5"}
        ],
        value="5",
        style={"width": "50%", "margin": "10px 0", "font-family": "Roboto, sans-serif"}
    ),
    dcc.Checklist(
        id="graph-selector",
        options=[
            {"label": "Температура", "value": "temperature"},
            {"label": "Влажность", "value": "humidity"},
            {"label": "Вероятность осадков", "value": "probability_of_precipitation"}
        ],
        value=["temperature", "humidity", "probability_of_precipitation"],
        style={"color": "#003366", "font-family": "Roboto, sans-serif"}
    ),
    html.Div(id="graphs-container",
             style={"display": "flex",
                    "flex-direction": "row",
                    "justify-content": "center"}),
    html.Label("Выберите дату для отображения прогноза:", style={"color": "#003366", "font-family": "Roboto, sans-serif"}),
    dcc.Dropdown(
        id="date-dropdown",
        options=[],
        value=None,
        style={"width": "50%", "margin": "10px 0", "font-family": "Roboto, sans-serif"}
    ),
    dcc.Graph(id="weather-map", style={"height": "700px"})
], style={"padding": "20px 100px"})


@app.callback(
    Output("graphs-container", "children"),
    Input("city-dropdown", "value"),
    Input("days-dropdown", "value"),
    Input("graph-selector", "value")
)
def update_graph(selected_city: str, selected_days: str, selected_graphs: list[str]) -> list[dcc.Graph]:
    if not selected_city or df.empty:
        return []
    filtered_df = get_filtered_df(selected_city, selected_days)
    graphs = []
    if "temperature" in selected_graphs:
        temp_graph = get_graph(filtered_df, "temperature",
                               f"Температура в городе {selected_city}", f"Температура (°C)")
        graphs.append(temp_graph)
    if "humidity" in selected_graphs:
        humidity_graph = get_graph(filtered_df, "humidity",
                               f"Влажность в городе {selected_city}", f"Влажность (%)")
        graphs.append(humidity_graph)
    if "probability_of_precipitation" in selected_graphs:
        pop_graph = get_graph(filtered_df, "probability_of_precipitation",
                              f"Вероятность осадков в городе {selected_city}", f"Вероятность осадков (%)")
        graphs.append(pop_graph)
    return graphs


def get_filtered_df(city: str, days: str):
    filtered_df = df[df["city_name"] == city]
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])
    filtered_df["probability_of_precipitation"] = filtered_df["probability_of_precipitation"] * 100
    if days == "1":
        filtered_df = filtered_df.head(1)
    elif days == "3":
        filtered_df = filtered_df.head(3)
    return filtered_df


def get_graph(data: pd.DataFrame, y: str, title: str, y_label: str) -> dcc.Graph:
    fig_func = px.bar if y == "probability_of_precipitation" else px.line
    params = {
        "x": "date",
        "y": y,
        "title": title,
        "labels": {y: y_label, "date": "Дата"}
    }
    if fig_func != px.bar:
        params["markers"] = True
    fig = fig_func(
        data,
        **params
    )

    fig.update_xaxes(
        tickformat="%Y-%m-%d",
        dtick="D1",
        tickangle=-45,
    )
    return dcc.Graph(figure=fig, style={"width": "500px", "height": "400px"})


@app.callback(
    Output("weather-map", "figure"),
    Input("date-dropdown", "value"),
)
def update_map(selected_date: str) -> go.Figure:
    filtered_df = df[df["date"] == selected_date]
    if filtered_df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=filtered_df["lat"],
        lon=filtered_df["lon"],
        mode="lines+markers",
        line=dict(width=2),
        marker=dict(size=10),
        name="Маршрут",
        hoverinfo="text",
        text=[
            f"{row["city_name"]}<br>Температура: {row["temperature"]}°C<br>Влажность: {row["humidity"]}%<br>Вероятность осадков: {row["probability_of_precipitation"] * 100}%"
            for _, row in filtered_df.iterrows()
        ]
    ))
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=5,
            center={"lat": filtered_df["lat"].iloc[0], "lon": filtered_df["lon"].iloc[0]}
        ),
        showlegend=True,
        title=f"Прогноз погоды на {selected_date}"
    )
    return fig


@app.callback(
    Output("city-dropdown", "options"),
    Output("city-dropdown", "value"),
    Output("date-dropdown", "options"),
    Output("date-dropdown", "value"),
    Input("city-dropdown", "id")
)
def update_dropdown_options(_) -> (list[str], str, list[str], str):
    if df.empty:
        return [], None, [], None
    unique_cities = df["city_name"].unique()
    options_cities = [{"label": city, "value": city} for city in unique_cities]
    default_city_value = unique_cities[0]

    unique_dates = df["date"].unique()
    options_dates = [{"label": date, "value": date} for date in unique_dates]
    default_date_value = unique_dates[0]

    return options_cities, default_city_value, options_dates, default_date_value


@server.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    if not is_connected():
        error_message = "Нет подключения к интернету."
        return render_template("index.html", error_message=error_message)
    cities = get_cities_from_request()
    if cities is None:
        error_message = "Пожалуйста, введите названия обоих городов."
        return render_template("index.html", error_message=error_message)
    try:
        cities_data, error_message = get_cities_forecasts_with_coords(cities)
        if error_message:
            return render_template("index.html", error_message=error_message)
    except requests.RequestException:
        error_message = "Произошла ошибка во время получения данных"
        return render_template("index.html", error_message=error_message)
    global df
    df = pd.DataFrame(columns=list(cities_data[0].keys()), data=cities_data)
    return redirect(url_for("dash_view"))


def get_cities_from_request() -> list[str] | None:
    departure_city = request.form.get("departureCity", "").capitalize()
    destination_city = request.form.get("destinationCity", "").capitalize()
    additional_cities = request.form.get("additionalCities", [])
    if not departure_city or not destination_city:
        return None
    if additional_cities:
        additional_cities = [city.strip().capitalize() for city in additional_cities.split(",")]
    return [departure_city, *additional_cities, destination_city]


def get_cities_forecasts_with_coords(cities: list[str]) -> (list[dict] | None, str):
    weather_service = WeatherService(config.api_key)
    geocoder = Geocoder(config.api_key)
    cities_data = []
    for city in cities:
        weather = weather_service.get_forecast_for(city, 5)
        if weather is None:
            error_message = f"Не удалось получить данные для города: {city}"
            return None, error_message
        lat, lon = geocoder.get_coordinates_by_city(city)
        city_data = [{**forecast, "lat": lat, "lon": lon, "city_name": city} for forecast in weather]
        cities_data.extend(city_data)
    return cities_data, ""
    

@server.route("/dash/")
def dash_view():
    return app.index()