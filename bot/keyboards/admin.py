from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Overview"), KeyboardButton(text="Players")],
            [KeyboardButton(text="Matches"), KeyboardButton(text="Results")],
            [KeyboardButton(text="Rankings"), KeyboardButton(text="Administration")],
            [KeyboardButton(text="Activity Log")],
            [KeyboardButton(text="Back to Player Menu")],
        ],
        resize_keyboard=True,
    )
