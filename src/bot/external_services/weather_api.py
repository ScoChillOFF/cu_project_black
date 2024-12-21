import asyncio
from pprint import pprint

import aiohttp
from aiohttp.web_exceptions import HTTPServiceUnavailable


class WeatherApi:
    base_url = "http://127.0.0.1:5000/api/forecasts"

    async def get_weather_for(self, city: str, days: int = 5, timeout: int = 5) -> list[dict] | None:
        """Возвращает прогноз на заданное количество дней, если город найден. Иначе None.
           Выбрасывает ValueError, если передано некорректное число дней,
                       TimeoutError, если превышено время ожидания,
                       ClientConnectionError, если произошла другая ошибка при подключении
                       HTTPServiceUnavailable, если сервис погоды не может получить данные"""
        if not (1 <= days <= 5):
            raise ValueError("Days must be between 1 and 5")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
            async with session.get(f"{self.base_url}/{city}?days={days}") as r:
                if r.status == 404:
                    return None
                if r.status == 503:
                    raise HTTPServiceUnavailable
                return await r.json()


async def test_weather_api():
    pprint(await WeatherApi().get_weather_for("Москва", 5))


if __name__ == "__main__":
    asyncio.run(test_weather_api())
