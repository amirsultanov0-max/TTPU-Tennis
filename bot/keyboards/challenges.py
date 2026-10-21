from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


PAGE_SIZE = 8


def get_opponents_keyboard(
    opponents,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Build a paginated opponent-selection keyboard."""

    start = page * PAGE_SIZE
    page_opponents = opponents[start:start + PAGE_SIZE]
    rows = [
        [
            InlineKeyboardButton(
                text=f"{player.first_name} {player.last_name}",
                callback_data=f"challenge:select:{player.id}",
            )
        ]
        for player in page_opponents
    ]

    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="Previous",
                callback_data=f"challenge:page:{page - 1}",
            )
        )
    if start + PAGE_SIZE < len(opponents):
        navigation.append(
            InlineKeyboardButton(
                text="Next",
                callback_data=f"challenge:page:{page + 1}",
            )
        )
    if navigation:
        rows.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_challenge_confirmation_keyboard(
    opponent_id: int,
) -> InlineKeyboardMarkup:
    """Return the keyboard for confirming a challenge."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Send challenge",
                    callback_data=f"challenge:confirm:{opponent_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Back to players",
                    callback_data="challenge:back",
                ),
            ],
        ]
    )


def get_challenge_request_keyboard(
    challenge_id: int,
) -> InlineKeyboardMarkup:
    """Return the keyboard for responding to a challenge."""

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
