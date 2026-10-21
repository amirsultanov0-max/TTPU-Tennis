from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.challenges import (
    PAGE_SIZE,
    get_challenge_confirmation_keyboard,
    get_challenge_request_keyboard,
    get_opponents_keyboard,
)
from bot.keyboards.matches import get_match_actions_keyboard
from bot.ui.components.buttons import MAIN_MENU_FIND_OPPONENT
from services.challenges import (
    accept_challenge,
    create_challenge,
    reject_challenge,
)
from services.ranking import get_player_rank
from services.users import (
    get_user_by_id,
    get_other_users,
    get_user_by_telegram_id,
)

router = Router()


def build_opponents_message(opponents, page: int = 0) -> str:
    """Build the current page of the opponent list."""

    start = page * PAGE_SIZE
    page_opponents = opponents[start:start + PAGE_SIZE]

    lines = [
        "Find Opponent",
        "",
        "Choose a player to challenge.",
        "",
    ]

    for player in page_opponents:
        matches_played = player.wins + player.losses
        win_rate = (
            round(player.wins / matches_played * 100)
            if matches_played
            else 0
        )
        lines.append(
            f"{player.first_name} {player.last_name}\n"
            f"   {player.ranking_points} pts · "
            f"{player.wins}W–{player.losses}L · "
            f"{win_rate}% win rate"
        )

    total_pages = max(1, (len(opponents) + PAGE_SIZE - 1) // PAGE_SIZE)
    lines.extend(["", f"Page {page + 1} of {total_pages}"])
    return "\n".join(lines)


@router.message(F.text == MAIN_MENU_FIND_OPPONENT)
async def find_opponent_handler(message: Message):
    """Show registered players in ranking order."""

    user = await get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Please complete registration first.")
        return

    opponents = await get_other_users(user.id)

    if not opponents:
        await message.answer(
            "Find Opponent\n\nThere are no other registered players yet."
        )
        return

    await message.answer(
        build_opponents_message(opponents),
        reply_markup=get_opponents_keyboard(opponents),
    )


@router.callback_query(F.data.startswith("challenge:page:"))
async def opponent_page_handler(callback: CallbackQuery):
    """Navigate through the opponent list."""

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(
            "Please complete registration first.",
            show_alert=True,
        )
        return

    page = int(callback.data.split(":")[-1])
    opponents = await get_other_users(user.id)
    total_pages = max(1, (len(opponents) + PAGE_SIZE - 1) // PAGE_SIZE)

    if not opponents:
        await callback.message.edit_text(
            "Find Opponent\n\nThere are no other registered players yet."
        )
        await callback.answer()
        return

    page = max(0, min(page, total_pages - 1))
    await callback.message.edit_text(
        build_opponents_message(opponents, page),
        reply_markup=get_opponents_keyboard(opponents, page),
    )
    await callback.answer()


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

    rank, total_players = await get_player_rank(opponent.id)
    matches_played = opponent.wins + opponent.losses
    win_rate = (
        round(opponent.wins / matches_played * 100)
        if matches_played
        else 0
    )
    group_name = (
        opponent.group.name
        if opponent.group
        else "Group not set"
    )

    await callback.message.edit_text(
        f"🎾 Player Profile\n\n"
        f"{opponent.first_name} {opponent.last_name}\n"
        f"Rank {rank} of {total_players} · "
        f"{opponent.ranking_points} points\n\n"
        f"Match record\n"
        f"{opponent.wins} wins · {opponent.losses} losses\n"
        f"{matches_played} matches played · "
        f"{win_rate}% win rate\n\n"
        f"{group_name}\n\n"
        f"Send this player a challenge?",
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
        build_opponents_message(opponents),
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
        f"🎾 Challenge sent\n\n"
        f"You challenged {opponent.first_name} "
        f"{opponent.last_name}.\n\n"
        f"We'll let you know when they respond."
    )

    await callback.bot.send_message(
        opponent.telegram_id,
        f"🎾 Match Challenge\n\n"
        f"{user.first_name} {user.last_name} challenged you.\n"
        f"{user.ranking_points} points · "
        f"{user.wins}W–{user.losses}L\n\n"
        f"Would you like to accept?",
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

    challenger = await get_user_by_id(
        challenge.challenger_id
    )

    await callback.message.edit_text(
        f"🎾 Challenge accepted\n\n"
        f"You accepted {challenger.first_name if challenger else 'the player'}"
        f"{' ' + challenger.last_name if challenger else ''}'s challenge."
        f"\n\nNext step: agree on a date and time."
    )

    await callback.message.answer(
        "📅 Schedule the match\n\n"
        "Propose a date and time to get things started.",
        reply_markup=get_match_actions_keyboard(
            match.id,
            match.status,
        ),
    )

    if challenger:
        await callback.bot.send_message(
            challenger.telegram_id,
            f"🎾 Challenge accepted\n\n"
            f"{user.first_name} {user.last_name} accepted your challenge.\n\n"
            f"Next step: agree on a date and time.",
            reply_markup=get_match_actions_keyboard(
                match.id,
                match.status,
            ),
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
        "Challenge declined\n\n"
        "No match has been created."
    )

    challenger = await get_user_by_id(
        challenge.challenger_id
    )

    if challenger:
        await callback.bot.send_message(
            challenger.telegram_id,
            f"🎾 Challenge update\n\n"
            f"{user.first_name} {user.last_name} "
            f"declined your challenge.\n\n"
            f"No match has been created.",
        )

    await callback.answer()
