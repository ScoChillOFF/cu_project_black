from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from lexicons.ru import LEXICON_RU


router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    """Обрабатывает команду /start"""
    await message.answer(text=LEXICON_RU["command_start"])


@router.message(Command(commands="help"))
async def process_help_command(message: Message):
    """Обрабатывает команду /help"""
    await message.answer(text=LEXICON_RU["command_help"])