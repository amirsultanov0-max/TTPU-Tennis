from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards.admin import get_admin_menu_keyboard
from bot.keyboards.main_menu import get_main_menu_keyboard_for_user
from bot.ui.components.buttons import MAIN_MENU_ADMIN_PANEL
from services.admin import (
    is_active_admin,
    get_admin_overview,
    get_admin_player,
    get_admin_players,
)


router = Router()
PAGE_SIZE = 5


def dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Players", callback_data="admin:players:0")]
        ]
    )


def players_keyboard(page: int, pages: int, players: list) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{player.first_name} {player.last_name}",
                callback_data=f"admin:player:{player.id}",
            )
        ]
        for player in players
    ]

    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="← Previous",
                callback_data=f"admin:players:{page - 1}",
            )
        )
    if page + 1 < pages:
        navigation.append(
            InlineKeyboardButton(
                text="Next →",
                callback_data=f"admin:players:{page + 1}",
            )
        )
    if navigation:
        rows.append(navigation)

    rows.append(
        [InlineKeyboardButton(text="Back to Dashboard", callback_data="admin:dashboard")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def player_keyboard(player_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← Back to Players", callback_data="admin:players:0")],
            [InlineKeyboardButton(text="Back to Dashboard", callback_data="admin:dashboard")],
        ]
    )


async def authorized_overview(telegram_id: int) -> dict | None:
    return await get_admin_overview(telegram_id)


@router.message(Command("admin"))
async def admin_dashboard(message: Message) -> None:
    if message.from_user is None:
        return

    overview = await authorized_overview(message.from_user.id)
    if overview is None:
        await message.answer("Access denied.")
        return

    await message.answer(
        "Admin Dashboard\n\n"
        f"Role: {overview['role']}\n\n"
        f"Players: {overview['players']}\n"
        f"Total matches: {overview['matches']}\n\n"
        "Match status\n"
        f"Awaiting scheduling: {overview['awaiting_schedule']}\n"
        f"Scheduled: {overview['scheduled']}\n"
        f"Completed: {overview['completed']}\n\n"
        "Results awaiting confirmation: "
        f"{overview['pending_results']}",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.callback_query(F.data == "admin:dashboard")
async def admin_dashboard_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Access denied.", show_alert=True)
        return

    overview = await authorized_overview(callback.from_user.id)
    if overview is None:
        await callback.answer("Access denied.", show_alert=True)
        return

    if callback.message:
        await callback.message.edit_text(
            "Admin Dashboard\n\n"
            f"Role: {overview['role']}\n\n"
            f"Players: {overview['players']}\n"
            f"Total matches: {overview['matches']}\n\n"
            "Match status\n"
            f"Awaiting scheduling: {overview['awaiting_schedule']}\n"
            f"Scheduled: {overview['scheduled']}\n"
            f"Completed: {overview['completed']}\n\n"
            "Results awaiting confirmation: "
            f"{overview['pending_results']}",
            reply_markup=dashboard_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:players:"))
async def admin_players_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Access denied.", show_alert=True)
        return

    try:
        page = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer("Invalid page.", show_alert=True)
        return

    if page < 0:
        await callback.answer("Invalid page.", show_alert=True)
        return

    data = await get_admin_players(callback.from_user.id, page, PAGE_SIZE)
    if data is None:
        await callback.answer("Access denied.", show_alert=True)
        return

    if data["total"] == 0:
        text = "Players\n\nNo registered players yet."
    else:
        actual_page = min(data["page"], data["pages"] - 1)
        if actual_page != page:
            data = await get_admin_players(
                callback.from_user.id, actual_page, PAGE_SIZE
            )
            if data is None:
                await callback.answer("Access denied.", show_alert=True)
                return

        text = (
            "Players\n\n"
            f"Registered players: {data['total']}\n"
            f"Page {data['page'] + 1} of {data['pages']}\n\n"
            "Select a player to view their profile."
        )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=players_keyboard(
                data["page"], data["pages"], data["players"]
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:player:"))
async def admin_player_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Access denied.", show_alert=True)
        return

    try:
        player_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer("Invalid player.", show_alert=True)
        return

    data = await get_admin_player(callback.from_user.id, player_id)
    if data is None:
        await callback.answer("Access denied.", show_alert=True)
        return

    if data.get("not_found"):
        await callback.answer("Player not found.", show_alert=True)
        return

    player = data["player"]
    group = data["group"]
    username = (
        f"@{player.telegram_username}"
        if player.telegram_username
        else "Not set"
    )
    phone = player.phone or "Not provided"

    text = (
        f"Player Profile\n\n"
        f"Name: {player.first_name} {player.last_name}\n"
        f"Student ID: {player.student_id}\n"
        f"Group: {group.name}\n"
        f"Telegram: {username}\n"
        f"Phone: {phone}\n\n"
        f"Ranking points: {player.ranking_points}\n"
        f"ELO rating: {player.elo_rating}\n"
        f"Wins: {player.wins}\n"
        f"Losses: {player.losses}\n"
        f"Matches played (ELO): {player.elo_matches_played}"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=player_keyboard(player.id),
        )
    await callback.answer()


@router.message(F.text == MAIN_MENU_ADMIN_PANEL)
async def open_admin_panel(message: Message) -> None:
    if message.from_user is None:
        return
    if not await is_active_admin(message.from_user.id):
        await message.answer(
            "Access denied.",
            reply_markup=await get_main_menu_keyboard_for_user(message.from_user.id),
        )
        return

    await message.answer(
        "Admin Panel\n\nChoose a section.",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.message(F.text == "Overview")
async def admin_overview_menu(message: Message) -> None:
    if message.from_user is None:
        return
    overview = await get_admin_overview(message.from_user.id)
    if overview is None:
        await message.answer("Access denied.")
        return

    await message.answer(
        "Admin Overview\n\n"
        f"Role: {overview['role']}\n\n"
        f"Players: {overview['players']}\n"
        f"Total matches: {overview['matches']}\n\n"
        "Match status\n"
        f"Awaiting scheduling: {overview['awaiting_schedule']}\n"
        f"Scheduled: {overview['scheduled']}\n"
        f"Completed: {overview['completed']}\n\n"
        f"Results awaiting confirmation: {overview['pending_results']}",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.message(F.text == "Players")
async def admin_players_menu(message: Message) -> None:
    if message.from_user is None:
        return
    data = await get_admin_players(message.from_user.id, 0, PAGE_SIZE)
    if data is None:
        await message.answer("Access denied.")
        return

    if data["total"] == 0:
        text = "Players\n\nNo registered players yet."
    else:
        text = (
            "Players\n\n"
            f"Registered players: {data['total']}\n"
            f"Page 1 of {data['pages']}\n\n"
            "Select a player to view their profile."
        )

    await message.answer(
        text,
        reply_markup=players_keyboard(
            data["page"], data["pages"], data["players"]
        ),
    )
    await message.answer(
        "Admin menu",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.message(F.text == "Back to Player Menu")
async def back_to_player_menu(message: Message) -> None:
    if message.from_user is None:
        return
    if not await is_active_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    await message.answer(
        "Player menu",
        reply_markup=await get_main_menu_keyboard_for_user(message.from_user.id),
    )


@router.message(
    F.text.in_({"Matches", "Results", "Administration", "Activity Log"})
)
async def admin_section_placeholder(message: Message) -> None:
    if message.from_user is None:
        return
    if not await is_active_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    await message.answer(
        f"{message.text}\n\nThis section is not implemented yet.",
        reply_markup=get_admin_menu_keyboard(),
    )
