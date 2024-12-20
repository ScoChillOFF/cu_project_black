from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp.client_exceptions import ClientConnectionError

from asyncio.exceptions import TimeoutError

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
    weather_api = WeatherApi()
    city = message.text
    days = await state.get_value("days", 5)
    try:
        forecast = await weather_api.get_weather_for(city=city, days=days)
    except (TimeoutError, ClientConnectionError):
        await message.answer(LEXICON_RU["weather_service_error"])
        return
    if forecast is None:
        await message.answer(LEXICON_RU["city_not_found_error"])
        return
    await state.update_data({city: forecast, "route": [city]})
    await message.answer(LEXICON_RU["fill_destination_city"])
    await state.set_state(FSMWeatherForm.fill_destination_city)


@router.message(StateFilter(FSMWeatherForm.fill_destination_city), F.text)
async def process_destination_city_input(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU["confirm"], reply_markup=get_confirm_kb())
    await state.set_state(FSMWeatherForm.confirm)


@router.callback_query(StateFilter(FSMWeatherForm.confirm), F.data == "view_route")
async def process_view_route_option(callback: CallbackQuery):
    await callback.answer()
    kb_builder = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text="Назад", callback_data="back_to_confirm")
    )
    await callback.message.edit_text(text="маршрут", reply_markup=kb_builder.as_markup())


@router.callback_query(StateFilter(FSMWeatherForm.confirm), F.data == "new_point")
async def process_new_point_option(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(text=LEXICON_RU["fill_additional_city"])
    await state.set_state(FSMWeatherForm.fill_additional_city)


@router.message(StateFilter(FSMWeatherForm.fill_additional_city), F.text)
async def process_additional_city_input(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU["additional_city_success"])
    await message.answer(LEXICON_RU["confirm"], reply_markup=get_confirm_kb())
    await state.set_state(FSMWeatherForm.confirm)


@router.callback_query(StateFilter(FSMWeatherForm.confirm, FSMWeatherForm.fill_additional_city),
                       F.data == "back_to_confirm")
async def process_back_to_confirm_option(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(text=LEXICON_RU["confirm"], reply_markup=get_confirm_kb())
    await state.set_state(FSMWeatherForm.confirm)


@router.callback_query(StateFilter(FSMWeatherForm.confirm), F.data == "confirm")
async def process_confirm_view(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(text="вывод прогноза")
    await callback.message.answer(LEXICON_RU["finished_forecast"])
    await state.set_state(default_state)
