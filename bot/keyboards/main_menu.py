from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.ui.components.buttons import (
    MAIN_MENU_BOOK_COURT,
    MAIN_MENU_FIND_OPPONENT,
    MAIN_MENU_MY_MATCHES,
    MAIN_MENU_MY_PROFILE,
    MAIN_MENU_RANKINGS,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Return the main TTPU Tennis navigation menu.
    """

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=MAIN_MENU_MY_PROFILE
                ),
                KeyboardButton(
                    text=MAIN_MENU_RANKINGS
                ),
            ],
            [
                KeyboardButton(
                    text=MAIN_MENU_MY_MATCHES
                ),
                KeyboardButton(
                    text=MAIN_MENU_FIND_OPPONENT
                ),
            ],
            [
                KeyboardButton(
                    text=MAIN_MENU_BOOK_COURT
                ),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
