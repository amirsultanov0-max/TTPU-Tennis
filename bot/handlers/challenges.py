from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.challenges import (
    get_challenge_confirmation_keyboard,
    get_challenge_request_keyboard,
    get_opponents_keyboard,
)
from bot.keyboards.matches import get_match_detail_keyboard
from bot.ui.components.buttons import MAIN_MENU_FIND_OPPONENT
from services.challenges import (
    accept_challenge,
    create_challenge,
    reject_challenge,
)
from services.users import (
    get_other_users,
    get_user_by_telegram_id,
)

router = Router()


@router.message(F.text == MAIN_MENU_FIND_OPPONENT)
async def find_opponent_handler(message: Message):
    """
    Show registered players that can be challenged.
    """

    user = await get_user_by_telegram_id(
        message.from_user.id
    )

    if not user:
        await message.answer(
            "Please complete registration first."
        )
        return

    opponents = await get_other_users(user.id)

    if not opponents:
        await message.answer(
            "There are no other registered players yet."
        )
        return

    await message.answer(
        "🎾 Choose an opponent",
        reply_markup=get_opponents_keyboard(opponents),
    )


@router.callback_query(
    F.data.startswith("challenge:select:")
)
async def select_opponent_handler(
    callback: CallbackQuery,
):
    """
    Show confirmation before creating a challenge.
    """

    opponent_id = int(
        callback.data.split(":")[-1]
    )

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Please complete registration first.",
            show_alert=True,
        )
        return

    opponents = await get_other_users(user.id)

    opponent = next(
        (
            opponent
            for opponent in opponents
            if opponent.id == opponent_id
        ),
        None,
    )

    if not opponent:
        await callback.answer(
            "Opponent not found.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        f"Challenge {opponent.first_name} "
        f"{opponent.last_name}?",
        reply_markup=get_challenge_confirmation_keyboard(
            opponent.id
        ),
    )

    await callback.answer()


@router.callback_query(F.data == "challenge:back")
async def challenge_back_handler(
    callback: CallbackQuery,
):
    """
    Return to the opponent list.
    """

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Please complete registration first.",
            show_alert=True,
        )
        return

    opponents = await get_other_users(user.id)

    if not opponents:
        await callback.message.edit_text(
            "There are no other registered players yet."
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "🎾 Choose an opponent",
        reply_markup=get_opponents_keyboard(opponents),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("challenge:confirm:")
)
async def confirm_challenge_handler(
    callback: CallbackQuery,
):
    """
    Create a challenge and notify the opponent.
    """

    opponent_id = int(
        callback.data.split(":")[-1]
    )

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Please complete registration first.",
            show_alert=True,
        )
        return

    opponents = await get_other_users(user.id)

    opponent = next(
        (
            player
            for player in opponents
            if player.id == opponent_id
        ),
        None,
    )

    if not opponent:
        await callback.answer(
            "Opponent not found.",
            show_alert=True,
        )
        return

    try:
        challenge = await create_challenge(
            challenger_id=user.id,
            opponent_id=opponent.id,
        )
    except ValueError as exc:
        await callback.answer(
            str(exc),
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        f"Challenge sent to "
        f"{opponent.first_name} {opponent.last_name}."
    )

    await callback.bot.send_message(
        opponent.telegram_id,
        f"🎾 {user.first_name} {user.last_name} "
        "challenged you to a match.",
        reply_markup=get_challenge_request_keyboard(
            challenge.id
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("challenge:accept:")
)
async def accept_challenge_handler(
    callback: CallbackQuery,
):
    """
    Accept a challenge and create the match.
    """

    challenge_id = int(
        callback.data.split(":")[-1]
    )

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Please complete registration first.",
            show_alert=True,
        )
        return

    try:
        challenge, match = await accept_challenge(
            challenge_id=challenge_id,
            user_id=user.id,
        )
    except ValueError as exc:
        await callback.answer(
            str(exc),
            show_alert=True,
        )
        return

    challenger = await get_user_by_telegram_id(
        challenge.challenger_id
    )

    await callback.message.edit_text(
        "Challenge accepted."
    )

    await callback.message.answer(
        "📅 Schedule the match",
        reply_markup=get_match_detail_keyboard(
            match
        ),
    )

    if challenger:
        await callback.bot.send_message(
            challenger.telegram_id,
            f"{user.first_name} {user.last_name} "
            "accepted your challenge.",
        )

    await callback.answer()


@router.callback_query(
    F.data.startswith("challenge:reject:")
)
async def reject_challenge_handler(
    callback: CallbackQuery,
):
    """
    Reject a challenge.
    """

    challenge_id = int(
        callback.data.split(":")[-1]
    )

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Please complete registration first.",
            show_alert=True,
        )
        return

    try:
        challenge = await reject_challenge(
            challenge_id=challenge_id,
            user_id=user.id,
        )
    except ValueError as exc:
        await callback.answer(
            str(exc),
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "Challenge declined."
    )

    challenger = await get_user_by_telegram_id(
        challenge.challenger_id
    )

    if challenger:
        await callback.bot.send_message(
            challenger.telegram_id,
            f"{user.first_name} {user.last_name} "
            "declined your challenge.",
        )

    await callback.answer()
