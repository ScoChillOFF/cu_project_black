from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_confirm_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text="Добавить точку", callback_data="new_point"),
        InlineKeyboardButton(text="Просмотреть маршрут", callback_data="view_route"),
        InlineKeyboardButton(text="Показать прогноз", callback_data="confirm"), width=2
    )
    return kb_builder.as_markup()