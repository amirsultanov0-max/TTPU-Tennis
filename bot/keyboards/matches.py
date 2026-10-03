from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# ============================================================
# MY MATCHES
# ============================================================


def get_my_matches_keyboard() -> InlineKeyboardMarkup:
    """Return the main My Matches navigation keyboard."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Upcoming",
                    callback_data="matches:upcoming",
                ),
                InlineKeyboardButton(
                    text="Needs Action",
                    callback_data="matches:needs_action",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Completed",
                    callback_data="matches:completed",
                ),
                InlineKeyboardButton(
                    text="Cancelled",
                    callback_data="matches:cancelled",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Refresh",
                    callback_data="matches:refresh",
                )
            ],
        ]
    )

# ============================================================
# MATCH LISTS
# ============================================================


def get_upcoming_matches_keyboard(
    previous_index: int | None,
    next_index: int | None,
    current_index: int,
) -> InlineKeyboardMarkup:
    """Return navigation controls for upcoming match pages."""

    buttons: list[list[InlineKeyboardButton]] = []

    navigation: list[InlineKeyboardButton] = []

    if previous_index is not None:
        navigation.append(
            InlineKeyboardButton(
                text="← Earlier",
                callback_data=(
                    f"matches:upcoming:previous:"
                    f"{previous_index}"
                ),
            )
        )

    if next_index is not None:
        navigation.append(
            InlineKeyboardButton(
                text="View Later →",
                callback_data=(
                    f"matches:upcoming:next:"
                    f"{current_index}:"
                    f"{next_index}"
                ),
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data="matches:back",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def get_completed_matches_keyboard(
    page: int,
    has_older: bool,
) -> InlineKeyboardMarkup:
    """Return navigation controls for completed match history."""

    buttons: list[list[InlineKeyboardButton]] = []

    navigation: list[InlineKeyboardButton] = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="← Previous",
                callback_data=f"matches:completed:page:{page - 1}",
            )
        )

    if has_older:
        navigation.append(
            InlineKeyboardButton(
                text="Next →",
                callback_data=f"matches:completed:page:{page + 1}",
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data="matches:back",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def get_match_list_keyboard(
    matches,
    prefix: str,
) -> InlineKeyboardMarkup:
    """
    Return a keyboard containing one button per match.

    The prefix identifies the My Matches section
    currently being viewed.
    """

    buttons: list[list[InlineKeyboardButton]] = []

    for match in matches:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Match #{match.id}",
                    callback_data=(
                        f"matches:view:{prefix}:{match.id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data="matches:back",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# MATCH ACTIONS
# ============================================================


def get_match_actions_keyboard(
    match_id: int,
    status: str,
) -> InlineKeyboardMarkup:
    """
    Return the available scheduling actions for a match.

    awaiting_schedule:
        - Propose date & time
        - Cancel match

    scheduled:
        - Change date & time
        - Cancel match

    completed:
        - No scheduling actions

    cancelled:
        - No scheduling actions
    """

    buttons: list[list[InlineKeyboardButton]] = []

    if status == "awaiting_schedule":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Propose date & time",
                    callback_data=(
                        f"matches:propose_schedule:{match_id}"
                    ),
                )
            ]
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text="Cancel match",
                    callback_data=(
                        f"matches:cancel:{match_id}"
                    ),
                )
            ]
        )

    elif status == "scheduled":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Change date & time",
                    callback_data=(
                        f"matches:change_schedule:{match_id}"
                    ),
                )
            ]
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text="Cancel match",
                    callback_data=(
                        f"matches:cancel:{match_id}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# RESULT ACTIONS
# ============================================================


def get_result_actions_keyboard(
    match_id: int,
    result_status: str,
    can_confirm: bool = False,
) -> InlineKeyboardMarkup:
    """
    Return result-related actions for a match.

    not_submitted:
        - Submit Result

    pending_confirmation:
        - Confirm Result
        - Dispute Result

    confirmed:
        - No result actions
    """

    buttons: list[list[InlineKeyboardButton]] = []

    if result_status == "not_submitted":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Submit Result",
                    callback_data=(
                        f"matches:submit_result:{match_id}"
                    ),
                )
            ]
        )

    elif (
        result_status == "pending_confirmation"
        and can_confirm
    ):
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Confirm Result",
                    callback_data=(
                        f"matches:confirm_result:{match_id}"
                    ),
                )
            ]
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text="Dispute Result",
                    callback_data=(
                        f"matches:dispute_result:{match_id}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# UPCOMING MATCH NAVIGATION
# ============================================================


def get_match_navigation_keyboard(
    match_id: int,
    section: str,
    status: str,
) -> InlineKeyboardMarkup:
    """
    Return scheduling actions and navigation for an
    individual Upcoming match.
    """

    buttons: list[list[InlineKeyboardButton]] = []

    actions = get_match_actions_keyboard(
        match_id=match_id,
        status=status,
    )

    buttons.extend(
        actions.inline_keyboard
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data=(
                    f"matches:list:{section}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# RESULT MATCH NAVIGATION
# ============================================================


def get_result_navigation_keyboard(
    match_id: int,
    section: str,
    result_status: str,
    can_confirm: bool = False,
) -> InlineKeyboardMarkup:
    """
    Return result actions and navigation for a
    Needs Action match.
    """

    buttons: list[list[InlineKeyboardButton]] = []

    actions = get_result_actions_keyboard(
        match_id=match_id,
        result_status=result_status,
        can_confirm=can_confirm,
    )

    buttons.extend(
        actions.inline_keyboard
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data=(
                    f"matches:list:{section}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# CANCEL CONFIRMATION
# ============================================================


def get_cancel_confirmation_keyboard(
    match_id: int,
    section: str,
) -> InlineKeyboardMarkup:
    """
    Return the cancellation confirmation keyboard.

    The section is preserved so the user can return to
    the correct My Matches section after cancelling or
    keeping the match.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, cancel",
                    callback_data=(
                        f"matches:confirm_cancel:"
                        f"{section}:{match_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text="Keep match",
                    callback_data=(
                        f"matches:keep:"
                        f"{section}:{match_id}"
                    ),
                ),
            ]
        ]
    )
