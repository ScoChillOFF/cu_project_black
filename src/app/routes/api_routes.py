from flask import Blueprint, request, jsonify

from services.weather import WeatherService
from config import config
from requests import RequestException


router = Blueprint("api", __name__)


@router.route("/forecasts/<string:city>", methods=["GET"])
def get_weather(city: str):
    days = request.args.get("days", 5)
    if not days or not days.isdigit() or not (1 <= int(days) <= 5):
        return jsonify({"reason": "Bad time interval provided. Must be a number between 1 and 5"}), 400

    weather_service = WeatherService(config.api_key)
    try:
        forecast = weather_service.get_forecast_for(city, int(days))
    except RequestException:
        return jsonify({"reason": "External service unavailable"}), 503
    if not forecast:
        return jsonify({"reason": "Not found"}), 404
    return forecast
