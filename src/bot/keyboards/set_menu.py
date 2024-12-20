from aiogram import Bot
from aiogram.types import BotCommand


async def set_main_menu(bot: Bot):
    """Настраивает кнопку Menu в левом нижнем углу"""
    main_menu_commands = [
        BotCommand(command='/help',
                   description='Справка по командам бота'),
        BotCommand(command='/weather',
                   description='Получить прогноз погоды'),
    ]
    await bot.set_my_commands(main_menu_commands)