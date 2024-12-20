from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    kb_builder = InlineKeyboardBuilder().row(
        *[InlineKeyboardButton(text=str(i), callback_data=str(i)) for i in range(1, 6)]
    )
    await message.answer(text=LEXICON_RU["command_weather"], reply_markup=kb_builder.as_markup())
    await state.set_state(FSMWeatherForm.fill_forecast_range)


@router.message(Command(commands="cancel"))
async def process_cancel_command(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU["command_cancel"])
    await state.set_state(default_state)
