from aiogram import Bot

from bot.ui.messages.matches import result_reminder_message
from services.matches import (
    get_matches_needing_result_reminder,
    mark_result_reminder_sent,
)


async def send_result_reminders(
    bot: Bot,
) -> None:
    """
    Send result reminders to players whose scheduled matches
    finished at least two hours ago.

    Each match is processed only if it has not already received
    a result reminder.
    """

    matches = await get_matches_needing_result_reminder()

    for match in matches:
        reminder_text = result_reminder_message(match)

        await bot.send_message(
            chat_id=match.player_one.telegram_id,
            text=reminder_text,
        )

        await bot.send_message(
            chat_id=match.player_two.telegram_id,
            text=reminder_text,
        )

        await mark_result_reminder_sent(
            match.id
        )
