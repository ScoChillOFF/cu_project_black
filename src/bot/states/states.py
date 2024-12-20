from aiogram.fsm.state import StatesGroup, State


class FSMWeatherForm(StatesGroup):
    fill_forecast_range = State()
    fill_departure_city = State()
    fill_destination_city = State()
    fill_additional_city = State()
    confirm = State()
