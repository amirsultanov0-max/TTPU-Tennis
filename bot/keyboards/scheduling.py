from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_schedule_request_keyboard(
    request_id: int,
) -> InlineKeyboardMarkup:
    """
    Return the keyboard for accepting or rejecting
    a schedule request.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Accept",
                    callback_data=f"scheduling:accept:{request_id}",
                ),
                InlineKeyboardButton(
                    text="Decline",
                    callback_data=f"scheduling:reject:{request_id}",
                ),
            ]
        ]
    )


def get_propose_another_time_keyboard(
    match_id: int,
) -> InlineKeyboardMarkup:
    """
    Return the keyboard for proposing another match time.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Propose another time",
                    callback_data=f"matches:propose_schedule:{match_id}",
                )
            ]
        ]
    )
