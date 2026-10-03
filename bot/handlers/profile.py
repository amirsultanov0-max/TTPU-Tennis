from aiogram import Router
from aiogram.types import CallbackQuery

from bot.ui.messages.common import profile_not_found_message
from bot.ui.messages.profile import profile_message
from services.users import get_user_by_telegram_id
from services.ranking import get_player_rank


router = Router()


@router.callback_query(lambda callback: callback.data == "menu:profile")
async def profile_handler(
    callback: CallbackQuery,
) -> None:
    """
    Show the student's tennis profile.
    """

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    rank, total_players = await get_player_rank(user.id)

    await callback.answer()

    await callback.message.answer(
        profile_message(user, rank, total_players)
    )
