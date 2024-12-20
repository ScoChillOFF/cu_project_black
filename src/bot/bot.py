import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config


async def main():
    logging.basicConfig(level=logging.INFO)

    storage = MemoryStorage()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=storage)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
