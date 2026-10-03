from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.rankings import get_rankings_keyboard
from bot.ui.components.buttons import MAIN_MENU_RANKINGS
from bot.ui.messages.rankings import rankings_message
from services.ranking import (
    get_rankings,
    get_total_players,
)


router = Router()


async def build_rankings_text() -> str:
    """
    Build the rankings message.
    """

    players = await get_rankings(
        limit=10
    )

    total_players = await get_total_players()

    return rankings_message(
        players,
        total_players,
    )


@router.message(F.text == MAIN_MENU_RANKINGS)
async def rankings_handler(
    message: Message,
) -> None:
    """
    Show the current tennis rankings.
    """

    rankings_text = await build_rankings_text()

    await message.answer(
        rankings_text,
        reply_markup=get_rankings_keyboard(),
    )


@router.callback_query(
    F.data == "rankings:refresh",
)
async def refresh_rankings_handler(
    callback: CallbackQuery,
) -> None:
    """
    Refresh the rankings.
    """

    await callback.answer()

    rankings_text = await build_rankings_text()

    await callback.message.edit_text(
        rankings_text,
        reply_markup=get_rankings_keyboard(),
    )
