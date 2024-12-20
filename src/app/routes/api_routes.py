from flask import Blueprint, request, jsonify

from app.services.weather import WeatherService
from app.config import config


router = Blueprint("api", __name__)


@router.route("/forecasts/<string:city>", methods=["GET"])
def get_weather(city: str):
    days = request.args.get("days", 5)
    if not days or not days.isdigit() or not (1 <= int(days) <= 5):
        return jsonify({"reason": "Bad time interval provided. Must be a number between 1 and 5"}), 400

    weather_service = WeatherService(config.api_key)
    forecast = weather_service.get_forecast_for(city, int(days))
    if not forecast:
        return jsonify({"reason": "Not found"}), 404
    return forecast
