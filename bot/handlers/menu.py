from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.main_menu import get_main_menu_keyboard_for_user
from bot.ui.components.buttons import (
    MAIN_MENU_BOOK_COURT,
    MAIN_MENU_MY_PROFILE,
)
from bot.ui.messages.common import (
    book_court_message,
    profile_not_found_message,
)
from bot.ui.messages.profile import profile_message
from services.users import get_user_by_telegram_id
from services.ranking import get_player_rank


router = Router()


@router.message(F.text == MAIN_MENU_MY_PROFILE)
async def my_profile_handler(
    message: Message,
) -> None:
    """
    Show the current user's TTPU Tennis profile.
    """

    user = await get_user_by_telegram_id(
        message.from_user.id
    )

    if not user:
        await message.answer(
            profile_not_found_message(),
            reply_markup=await get_main_menu_keyboard_for_user(message.from_user.id),
        )
        return

    rank, total_players = await get_player_rank(user.id)

    await message.answer(
        profile_message(user, rank, total_players),
        reply_markup=await get_main_menu_keyboard_for_user(message.from_user.id),
    )


@router.message(F.text == MAIN_MENU_BOOK_COURT)
async def book_court_handler(
    message: Message,
) -> None:
    """
    Open the court booking section.
    """

    await message.answer(
        book_court_message(),
        reply_markup=await get_main_menu_keyboard_for_user(message.from_user.id),
    )
