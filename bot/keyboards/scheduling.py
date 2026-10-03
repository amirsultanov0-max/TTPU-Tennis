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
                    text="Reject",
                    callback_data=f"scheduling:reject:{request_id}",
                ),
            ]
        ]
    )


def get_match_schedule_keyboard(
    match_id: int,
) -> InlineKeyboardMarkup:
    """
    Return the keyboard for an unscheduled match.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Propose date & time",
                    callback_data=f"scheduling:propose:{match_id}",
                )
            ]
        ]
    )