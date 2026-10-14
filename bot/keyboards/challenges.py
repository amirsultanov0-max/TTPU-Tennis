from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_opponents_keyboard(
    opponents,
) -> InlineKeyboardMarkup:
    """
    Return a keyboard for selecting an opponent.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{opponent.first_name} {opponent.last_name}",
                    callback_data=f"challenge:select:{opponent.id}",
                )
            ]
            for opponent in opponents
        ]
    )


def get_challenge_confirmation_keyboard(
    opponent_id: int,
) -> InlineKeyboardMarkup:
    """
    Return the keyboard for confirming a challenge.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Challenge",
                    callback_data=f"challenge:confirm:{opponent_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Back",
                    callback_data="challenge:back",
                ),
            ],
        ]
    )


def get_challenge_request_keyboard(
    challenge_id: int,
) -> InlineKeyboardMarkup:
    """
    Return the keyboard for responding to a challenge.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Accept",
                    callback_data=f"challenge:accept:{challenge_id}",
                ),
                InlineKeyboardButton(
                    text="Decline",
                    callback_data=f"challenge:reject:{challenge_id}",
                ),
            ],
        ]
    )
