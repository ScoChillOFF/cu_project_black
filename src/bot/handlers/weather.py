from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from states.states import FSMWeatherForm
from lexicons.ru import LEXICON_RU


router = Router()
router.message.filter(StateFilter(FSMWeatherForm))


@router.message(StateFilter(FSMWeatherForm.fill_forecast_range), F.text)
async def process_forecast_range_input(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU["fill_departure_city"])
    await state.set_state(FSMWeatherForm.fill_departure_city)


@router.message(StateFilter(FSMWeatherForm.fill_departure_city), F.text)
async def process_departure_city_input(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU["fill_destination_city"])
    await state.set_state(FSMWeatherForm.fill_destination_city)


@router.message(StateFilter(FSMWeatherForm.fill_destination_city), F.text)
async def process_destination_city_input(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU["confirm"])
    await state.set_state(FSMWeatherForm.confirm)


@router.message(StateFilter(FSMWeatherForm.confirm), F.text)
async def process_confirm_view(message: Message, state: FSMContext):
    await message.answer("вывод прогноза")
    await message.answer(LEXICON_RU["finished_forecast"])
    await state.set_state(default_state)
