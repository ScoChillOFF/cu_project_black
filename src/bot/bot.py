import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from handlers.commands import router as commands_router
from handlers.weather import router as weather_router
from handlers.other import router as other_router
from keyboards.set_menu import set_main_menu


async def run_bot():
    logging.basicConfig(level=logging.INFO)

    storage = MemoryStorage()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=storage)

    dp.include_router(commands_router)
    dp.include_router(weather_router)
    dp.include_router(other_router)

    await set_main_menu(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
