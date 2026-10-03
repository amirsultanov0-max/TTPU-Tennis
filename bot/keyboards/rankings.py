from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_rankings_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for the rankings section.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Refresh",
                    callback_data="rankings:refresh",
                ),
            ],
        ]
    )
