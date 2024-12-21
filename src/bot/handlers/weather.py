from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp.client_exceptions import ClientConnectionError

from asyncio.exceptions import TimeoutError

from aiohttp.web_exceptions import HTTPServiceUnavailable

from external_services.weather_api import WeatherApi
from keyboards.inline import get_confirm_kb
from states.states import FSMWeatherForm
from lexicons.ru import LEXICON_RU


router = Router()
router.message.filter(StateFilter(FSMWeatherForm))


@router.callback_query(StateFilter(FSMWeatherForm.fill_forecast_range))
async def process_forecast_range_input(callback: CallbackQuery, state: FSMContext):
    """Сохраняет количество дней для прогноза и запрашивает следующий этап (ввод города отправления)"""
    await callback.answer()
    await state.update_data({"days": int(callback.data)})
    await callback.message.edit_text(LEXICON_RU["fill_departure_city"])
    await state.set_state(FSMWeatherForm.fill_departure_city)


@router.message(StateFilter(FSMWeatherForm.fill_departure_city), F.text)
async def process_departure_city_input(message: Message, state: FSMContext):
    """Сохраняет прогноз для города отправления, если его удалось получить, иначе запрашивает повторную попытку.
       Сохраняет маршрут (с одной точкой).
       Запрашивает ввод точки назначения, если успешно"""
    forecast = await process_city_input_and_get_forecast(message, state)
    if forecast is None:
        return
    city = message.text
    await state.update_data({city: forecast, "route": [city]})
    await message.answer(LEXICON_RU["fill_destination_city"])
    await state.set_state(FSMWeatherForm.fill_destination_city)


@router.message(StateFilter(FSMWeatherForm.fill_destination_city), F.text)
async def process_destination_city_input(message: Message, state: FSMContext):
    """Сохраняет прогноз для города назначения, если его удалось получить, иначе запрашивает повторную попытку.
       Сохраняет маршрут (с одной точкой).
       Показывает меню подтверждения прогноза, если успешно"""
    forecast = await process_city_input_and_get_forecast(message, state)
    if forecast is None:
        return
    city = message.text
    route = await state.get_value("route")
    route.append(city)
    await state.update_data({"route": route, city: forecast})
    await message.answer(LEXICON_RU["confirm"], reply_markup=get_confirm_kb())
    await state.set_state(FSMWeatherForm.confirm)


@router.callback_query(StateFilter(FSMWeatherForm.confirm), F.data == "view_route")
async def process_view_route_option(callback: CallbackQuery, state: FSMContext):
    """Отображает текущий маршрут"""
    await callback.answer()
    cities = await state.get_value("route")
    cities_text = "\n".join([f"\t{i}. {city.capitalize()}" for i, city in enumerate(cities, start=1)])
    text = LEXICON_RU["view_route"].format(cities_text)
    kb_builder = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text="Назад", callback_data="back_to_confirm")
    )
    await callback.message.edit_text(text=text, reply_markup=kb_builder.as_markup())


@router.callback_query(StateFilter(FSMWeatherForm.confirm), F.data == "new_point")
async def process_new_point_option(callback: CallbackQuery, state: FSMContext):
    """Перенаправляет на ввод промежуточной точки"""
    await callback.answer()
    await callback.message.edit_text(text=LEXICON_RU["fill_additional_city"])
    await state.set_state(FSMWeatherForm.fill_additional_city)


@router.message(StateFilter(FSMWeatherForm.fill_additional_city), F.text)
async def process_additional_city_input(message: Message, state: FSMContext):
    """Сохраняет прогноз для города назначения, если его удалось получить, иначе запрашивает повторную попытку.
           Сохраняет маршрут (с одной точкой).
           Показывает меню подтверждения прогноза, если успешно"""
    forecast = await process_city_input_and_get_forecast(message, state)
    if forecast is None:
        return
    route = await state.get_value("route")
    city = message.text
    route.insert(-1, city)
    await state.update_data({"route": route, city: forecast})
    await message.answer(text=LEXICON_RU["additional_city_success"])
    await message.answer(LEXICON_RU["confirm"], reply_markup=get_confirm_kb())
    await state.set_state(FSMWeatherForm.confirm)


@router.callback_query(StateFilter(FSMWeatherForm.confirm, FSMWeatherForm.fill_additional_city),
                       F.data == "back_to_confirm")
async def process_back_to_confirm_option(callback: CallbackQuery, state: FSMContext):
    """Показывает меню подтверждения прогноза"""
    await callback.answer()
    await callback.message.edit_text(text=LEXICON_RU["confirm"], reply_markup=get_confirm_kb())
    await state.set_state(FSMWeatherForm.confirm)


@router.callback_query(StateFilter(FSMWeatherForm.confirm), F.data == "confirm")
async def process_confirm_view(callback: CallbackQuery, state: FSMContext):
    """Показывает прогноз и очищает состояние"""
    await callback.answer()
    await callback.message.edit_text(text=LEXICON_RU["forecast_begin"])
    data = await state.get_data()
    for i, city in enumerate(data["route"], start=1):
        days_forecasts_texts = []
        for day in range(data["days"]):
            forecast = data[city][day]
            forecast_text = LEXICON_RU["forecast_day"].format(
                date=forecast["date"],
                temp=forecast["temperature"],
                wind=forecast["wind_speed"],
                pop=forecast["probability_of_precipitation"] * 100,
            )
            days_forecasts_texts.append(forecast_text)
        text = LEXICON_RU["forecast_city"].format(
            i=i,
            city=city.capitalize(),
            forecast="\n\n".join(days_forecasts_texts)
        )
        await callback.message.answer(text=text, parse_mode="html")
    await callback.message.answer(LEXICON_RU["finished_forecast"])
    await state.set_state(default_state)


async def process_city_input_and_get_forecast(message: Message, state: FSMContext) -> list[dict] | None:
    """Обрабатывает ввод города: проверяет, найден ли он и нет ли его уже в маршруте.
       В случае ошибки отправляет сообщение, в случае успеха возвращает прогноз"""
    weather_api = WeatherApi()
    city = message.text
    days = await state.get_value("days", 5)
    try:
        forecast = await weather_api.get_weather_for(city=city, days=days)
    except (TimeoutError, ClientConnectionError, HTTPServiceUnavailable):
        await message.answer(LEXICON_RU["weather_service_error"])
        return
    if forecast is None:
        await message.answer(LEXICON_RU["city_not_found_error"])
        return
    route = await state.get_value("route", [])
    if city.lower() in [c.lower() for c in route]:
        await message.answer(LEXICON_RU["city_repeat_error"])
        return
    return forecast
