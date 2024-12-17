import requests

from statistics import mean

from geocoder import Geocoder


class WeatherService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.geocoder = Geocoder(api_key)

    def get_forecast_for(self, city: str, days: int) -> list | None:
        if not (1 <= days <= 5):
            raise ValueError("Количество дней должно быть от 1 до 5")
        daily_5days_forecast = self._get_daily_5days_forecast(city)
        if daily_5days_forecast is None:
            return None
        return daily_5days_forecast[:days]

    def _get_daily_5days_forecast(self, city: str) -> list | None:
        hourly_forecast = self._get_3hourly_5days_forecast(city)
        if not hourly_forecast:
            return None
        daily_forecast = []
        for hourly_day_forecast in self._extract_daily_3hourly_forecast(hourly_forecast):
            day_forecast = self._make_1day_forecast(hourly_day_forecast)
            daily_forecast.append(day_forecast)
        return daily_forecast

    def _get_3hourly_5days_forecast(self, city: str) -> list | None:
        coords = self.geocoder.get_coordinates_by_city(city)
        if coords is None:
            return None
        lat, lon = coords

        url = f"http://api.openweathermap.org/data/2.5/forecast"
        r = requests.get(url, params={
            "appid": self.api_key,
            "lang": "ru",
            "units": "metric",
            "lat": lat,
            "lon": lon
        })
        r.raise_for_status()

        r_json = r.json()
        return r_json["list"]

    @staticmethod
    def _extract_daily_3hourly_forecast(hourly_forecast: list) -> list:
        daily_3hourly_forecast = []

        day_3hourly_forecast = []
        for epoch in hourly_forecast:
            if epoch["dt_txt"].split()[-1] == "00:00:00" and day_3hourly_forecast:
                daily_3hourly_forecast.append(epoch)

        return daily_3hourly_forecast

    def _make_1day_forecast(self, hourly_forecast: list) -> dict:
        day_forecast = {}
        day_forecast["temperature"] = round(
            mean([hfc["main"]["temp"] for hfc in hourly_forecast]), 1
        )
        day_forecast["wind_speed"] = round(
            mean([hfc["wind"]["speed"] for hfc in hourly_forecast]), 1
        )
        day_forecast["probability_of_precipitation"] = max(
            [hfc["pop"] for hfc in hourly_forecast]
        )
        day_forecast["humidity"] = round(
            mean([hfc["main"]["humidity"] for hfc in hourly_forecast])
        )
        day_forecast["date"] = hourly_forecast[0]["dt_txt"].split()[0]
        day_forecast["verdict"] = self._get_weather_verdict(day_forecast)
        return day_forecast

    def _get_weather_verdict(self, conditions: dict) -> str:
        if self._is_weather_good(conditions):
            return "Самое время для прогулки!"
        else:
            return "Прогулка не самый лучший выбор."

    @staticmethod
    def _is_weather_good(conditions: dict) -> bool:
        return all([
            0 <= conditions["temperature"] <= 35,
            conditions["wind_speed"] <= 50,
            conditions["probability_of_precipitation"] <= 70
        ])
