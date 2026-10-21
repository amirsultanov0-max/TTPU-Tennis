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


def get_schedule_accepted_keyboard() -> InlineKeyboardMarkup:
    """Return navigation after accepting a schedule request."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="My Matches",
                    callback_data="matches:back",
                )
            ],
        ]
    )


# ============================================================
# MATCH LISTS
# ============================================================


def get_upcoming_matches_keyboard(
    visible_matches,
    previous_index: int | None,
    next_index: int | None,
    current_index: int,
) -> InlineKeyboardMarkup:
    """Return match-selection and navigation controls for an upcoming page."""

    buttons: list[list[InlineKeyboardButton]] = []

    match_buttons: list[InlineKeyboardButton] = []

    for match in visible_matches:
        match_buttons.append(
            InlineKeyboardButton(
                text=f"Match #{match.id}",
                callback_data=(
                    f"matches:view:upcoming:{match.id}"
                ),
            )
        )

    for index in range(0, len(match_buttons), 2):
        buttons.append(match_buttons[index:index + 2])

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


def get_needs_action_keyboard(
    action_type: str,
    match_id: int | None = None,
    request_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Return actions for a Needs Action inbox item."""

    buttons: list[list[InlineKeyboardButton]] = []

    if action_type == "schedule":
        if match_id is None:
            raise ValueError("match_id is required for schedule actions.")

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{match_id} Propose Date & Time",
                    callback_data=(
                        f"matches:propose_schedule:{match_id}"
                    ),
                )
            ]
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{match_id} Cancel Match",
                    callback_data=(
                        f"matches:cancel:needs_action:{match_id}"
                    ),
                )
            ]
        )

    elif action_type == "schedule_proposal":
        if request_id is None:
            raise ValueError(
                "request_id is required for schedule proposals."
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{match_id} Accept",
                    callback_data=(
                        f"scheduling:accept:{request_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text=f"#{match_id} Decline",
                    callback_data=(
                        f"scheduling:reject:{request_id}"
                    ),
                ),
            ]
        )

    elif action_type == "result":
        if match_id is None:
            raise ValueError("match_id is required for result actions.")

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{match_id} Submit Result",
                    callback_data=f"matches:submit_result:{match_id}",
                ),
                InlineKeyboardButton(
                    text=f"#{match_id} Not Played",
                    callback_data=f"matches:not_played:request:{match_id}",
                ),
            ]
        )

    elif action_type == "not_played_pending":
        if match_id is None:
            raise ValueError("match_id is required for not-played responses.")

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{match_id} Confirm",
                    callback_data=f"matches:not_played:confirm:{match_id}",
                ),
                InlineKeyboardButton(
                    text="No, we played",
                    callback_data=f"matches:not_played:reject:{match_id}",
                ),
            ]
        )

    elif action_type == "confirmation":
        if match_id is None:
            raise ValueError(
                "match_id is required for result confirmation."
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{match_id} Confirm Result",
                    callback_data=(
                        f"matches:confirm_result:{match_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text=f"#{match_id} Report Issue",
                    callback_data=(
                        f"matches:dispute_result:{match_id}"
                    ),
                ),
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def get_result_reminder_keyboard(
    match_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Submit Result",
                    callback_data=(
                        f"matches:submit_result:{match_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="My Matches",
                    callback_data="matches:open",
                )
            ],
        ]
    )


# ============================================================
# MATCH ACTIONS
# ============================================================


def get_match_actions_keyboard(
    match_id: int,
    status: str,
    section: str = "upcoming",
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
                        f"matches:cancel:{section}:{match_id}"
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
                        f"matches:cancel:{section}:{match_id}"
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
        section=section,
    )

    buttons.extend(
        actions.inline_keyboard
    )

    back_callback = (
        "matches:upcoming"
        if section == "upcoming"
        else "matches:needs_action"
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data=back_callback,
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def get_cancelled_matches_keyboard(
    page: int,
    has_older: bool,
) -> InlineKeyboardMarkup:
    """Return navigation controls for cancelled match history."""

    buttons: list[list[InlineKeyboardButton]] = []

    navigation: list[InlineKeyboardButton] = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="← Previous",
                callback_data=f"matches:cancelled:page:{page - 1}",
            )
        )

    if has_older:
        navigation.append(
            InlineKeyboardButton(
                text="Next →",
                callback_data=f"matches:cancelled:page:{page + 1}",
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
