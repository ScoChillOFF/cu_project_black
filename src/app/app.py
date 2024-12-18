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
    dcc.Graph(id='my-graph'),
])


@app.callback(
    Output('my-graph', 'figure'),
    Input('my-graph', 'id')  # Используем входной параметр для триггера обновления
)
def update_graph(_):
    if not df.empty:
        # Предположим, что у вас есть столбцы 'date' и 'temperature' в DataFrame
        fig = px.line(df, x='date', y='temperature', title='Прогноз погоды')
        return fig
    return {}  # Возвращаем пустой график, если DataFrame пустой


@server.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    if request.method == 'POST':
        departure_city = request.form.get('departureCity')
        destination_city = request.form.get('destinationCity')
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
            lat, lon = geocoder.get_coordinates_by_city(city)
            weather = weather_service.get_forecast_for(city, 5)
            if weather is None:
                error_message = f"Не удалось получить данные для города: {departure_city}"
                return render_template("index.html", error_message=error_message)
            city_data = [{**forecast, "lat": lat, "lon": lon, "city_name": city} for forecast in weather]
            cities_data.extend(city_data)
        global df
        df = pd.DataFrame(columns=list(cities_data[0].keys()), data=cities_data)
        print(df)
        return redirect(url_for('dash_view'))


@server.route('/dash/')
def dash_view():
    return app.index()