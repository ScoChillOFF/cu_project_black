import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
import dash
import plotly.express as px
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
    html.H1("Прогноз погоды"),

    html.Label("Выберите город:"),
    dcc.Dropdown(id="city-dropdown", options=[], value=None),

    html.Label("Выберите количество дней для прогноза:"),
    dcc.Dropdown(
        id="days-dropdown",
        options=[
            {"label": "1 день", "value": "1"},
            {"label": "3 дня", "value": "3"},
            {"label": "5 дней", "value": "5"}
        ],
        value="5"
    ),

    dcc.Checklist(
        id="graph-selector",
        options=[
            {"label": "Температура", "value": "temperature"},
            {"label": "Влажность", "value": "humidity"},
            {"label": "Вероятность осадков", "value": "probability_of_precipitation"}
        ],
        value=["temperature", "humidity", "probability_of_precipitation"],
        inline=True 
    ),

    html.Div(id="graphs-container", style={"display": "flex", "flex-direction": "row", "justify-content": "center"})
])


@app.callback(
    Output("graphs-container", "children"),
    Input("city-dropdown", "value"),
    Input("days-dropdown", "value"),
    Input("graph-selector", "value")
)
def update_graph(selected_city, selected_days, selected_graphs):
    if selected_city and not df.empty:
        filtered_df = df[df["city_name"] == selected_city]
        filtered_df["date"] = pd.to_datetime(filtered_df["date"])
        filtered_df["probability_of_precipitation"] = filtered_df["probability_of_precipitation"] * 100

        if selected_days == "1":
            filtered_df = filtered_df.head(1)
        elif selected_days == "3":
            filtered_df = filtered_df.head(3)

        graphs = []

        if "temperature" in selected_graphs:
            fig_temp = px.line(
                filtered_df,
                x="date",
                y="temperature",
                title=f"Температура в городе {selected_city}",
                markers=True,
                labels={"temperature": "Температура (°C)", "date": "Дата"}
            )
    
            fig_temp.update_xaxes(
                tickformat="%Y-%m-%d",
                dtick="D1",
                tickangle=-45,
            )
            graphs.append(dcc.Graph(figure=fig_temp, style={"width": "500px", "height": "400px"}))

        if "humidity" in selected_graphs:
            fig_humidity = px.line(
                filtered_df,
                x="date",
                y="humidity",
                title=f"Влажность в городе {selected_city}",
                markers=True,
                labels={"humidity": "Влажность (%)", "date": "Дата"}
            )

            fig_humidity.update_xaxes(
                tickformat="%Y-%m-%d",
                dtick="D1",
                tickangle=-45
            )
            graphs.append(dcc.Graph(figure=fig_humidity, style={"width": "500px", "height": "400px"}))

        if "probability_of_precipitation" in selected_graphs:
            fig_pop = px.bar(
                filtered_df,
                x="date",
                y="probability_of_precipitation",
                title=f"Вероятность осадков в городе {selected_city}",
                labels={"probability_of_precipitation": "Вероятность осадков (%)", "date": "Дата"}
            )

            fig_pop.update_xaxes(
                tickformat="%Y-%m-%d",
                dtick="D1",
                tickangle=-45
            )
            graphs.append(dcc.Graph(figure=fig_pop, style={"width": "500px", "height": "400px"}))
        return graphs
    return {}, {}, {}


@app.callback(
    Output("city-dropdown", "options"),
    Output("city-dropdown", "value"),
    Input("city-dropdown", "id")
)
def update_dropdown_options(_):
    if not df.empty:
        unique_cities = df["city_name"].unique()
        options = [{"label": city, "value": city} for city in unique_cities]
        default_value = unique_cities[0]
        return options, default_value
    return [], None


@server.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    if request.method == "POST":
        departure_city = request.form.get("departureCity")
        destination_city = request.form.get("destinationCity")
        if not departure_city or not destination_city:
            error_message = "Пожалуйста, введите названия обоих городов."
            return render_template("index.html", error_message=error_message)
        if not is_connected():
            error_message = "Нет подключения к интернету."
            return render_template("index.html", error_message=error_message)
        weather_service = WeatherService(config.api_key)
        geocoder = Geocoder(config.api_key)
        cities_data = []
        for city in [departure_city, destination_city]:
            city = city.capitalize()
            lat, lon = geocoder.get_coordinates_by_city(city)
            weather = weather_service.get_forecast_for(city, 5)
            if weather is None:
                error_message = f"Не удалось получить данные для города: {city}"
                return render_template("index.html", error_message=error_message)
            city_data = [{**forecast, "lat": lat, "lon": lon, "city_name": city} for forecast in weather]
            cities_data.extend(city_data)
        global df
        df = pd.DataFrame(columns=list(cities_data[0].keys()), data=cities_data)
        return redirect(url_for("dash_view"))


@server.before_request
def check_data():
    if request.endpoint == "dash_view" and df.empty:
        return redirect(url_for("index")) 
    

@server.route("/dash/")
def dash_view():
    return app.index()