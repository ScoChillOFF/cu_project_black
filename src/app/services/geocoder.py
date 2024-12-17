import requests


class Geocoder:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_coordinates_by_city(self, city: str) -> tuple[float, float] | None:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={self.api_key}&limit=5"
        r = requests.get(url)

        if r.status_code != 200:
            return None
        r_json = r.json()
        if not r_json:
            return None

        city_data = r_json[0]
        return city_data["lat"], city_data["lon"]
