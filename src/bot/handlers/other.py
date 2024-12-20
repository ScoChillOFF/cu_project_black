from aiogram import Router
from aiogram.types import Message

from lexicons.ru import LEXICON_RU

router = Router()


@router.message()
async def process_wrong_input(message: Message):
    await message.answer(LEXICON_RU["wrong_input"])