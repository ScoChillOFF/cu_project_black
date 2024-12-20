from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from lexicons.ru import LEXICON_RU
from states.states import FSMWeatherForm


router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    """Обрабатывает команду /start"""
    await message.answer(text=LEXICON_RU["command_start"])


@router.message(Command(commands="help"))
async def process_help_command(message: Message):
    """Обрабатывает команду /help"""
    await message.answer(text=LEXICON_RU["command_help"])


@router.message(Command(commands="weather"))
async def process_weather_command(message: Message, state: FSMContext):
    """Обрабатывает команду /weather, перенаправляя на соответствующие обработчики"""
    await message.answer(text=LEXICON_RU["command_weather"])
    await state.set_state(FSMWeatherForm.fill_forecast_range)
