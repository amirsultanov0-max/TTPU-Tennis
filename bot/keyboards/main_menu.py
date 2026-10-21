from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.ui.components.buttons import (
    MAIN_MENU_BOOK_COURT,
    MAIN_MENU_ADMIN_PANEL,
    MAIN_MENU_FIND_OPPONENT,
    MAIN_MENU_MY_MATCHES,
    MAIN_MENU_MY_PROFILE,
    MAIN_MENU_RANKINGS,
)


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Return the main TTPU Tennis navigation menu.
    """

    keyboard = [
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
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text=MAIN_MENU_ADMIN_PANEL)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )



async def get_main_menu_keyboard_for_user(telegram_id: int) -> ReplyKeyboardMarkup:
    """Show the Admin Panel button only to active admins."""

    from services.admin import is_active_admin

    return get_main_menu_keyboard(
        is_admin=await is_active_admin(telegram_id)
    )
