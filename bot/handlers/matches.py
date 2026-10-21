import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

from bot.keyboards.matches import (
    get_cancelled_matches_keyboard,
    get_cancel_confirmation_keyboard,
    get_completed_matches_keyboard,
    get_needs_action_keyboard,
    get_upcoming_matches_keyboard,
    get_match_navigation_keyboard,
    get_result_actions_keyboard,
    get_my_matches_keyboard,
    get_schedule_accepted_keyboard,
)

from bot.states.matches import MatchResultStates
from bot.ui.components.buttons import MAIN_MENU_MY_MATCHES
from bot.ui.messages.common import (
    match_not_found_message,
    not_match_player_message,
    profile_not_found_message,
)

from bot.ui.messages.matches import (
    format_match_message,
    format_upcoming_match_detail,
    format_upcoming_match_summary,
    format_match_summary,
    format_cancelled_matches_message,
    match_empty_message,
    needs_action_header,
    format_needs_action_schedule,
    format_needs_action_schedule_proposal,
    format_needs_action_result,
    format_needs_action_not_played,
    format_needs_action_confirmation,
    my_matches_message,
    confirmed_result_message,
    result_submission_message,
    set_2_submission_message,
    set_3_submission_message,
    submitted_result_message,
    score_format_error_message,
    result_session_expired_message,
    invalid_match_result_message,
    score_parse_error_message,
    invalid_set_score_message
)


from services.matches import (
    cancel_match,
    confirm_match_result,
    get_match_by_id,
    get_player_match_stats,
    get_matches_for_user,
    get_pending_schedule_requests,
    request_match_not_played,
    confirm_match_not_played,
    reject_match_not_played,
    submit_match_result,
)
from services.users import get_user_by_telegram_id
from services.ranking import get_player_rank


logger = logging.getLogger(__name__)


router = Router()


# ============================================================
# SAFE MESSAGE EDIT
# ============================================================


async def safe_edit_text(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    """
    Edit a callback message safely.

    Telegram raises "message is not modified" when the new
    content and keyboard are identical to the current ones.
    That situation is harmless, so we silently ignore it.
    """

    try:
        await callback.message.edit_text(
            text,
            reply_markup=reply_markup,
        )

    except TelegramBadRequest as error:
        if "message is not modified" not in str(error):
            raise


# ============================================================
# MATCH STATUS
# ============================================================


def get_upcoming_matches(matches) -> list:
    """
    Return scheduled matches whose time has not passed.
    """

    now = datetime.now(timezone.utc)

    upcoming = []

    for match in matches:

        if (
            match.status == "scheduled"
            and match.scheduled_at
            and match.scheduled_at > now
        ):
            upcoming.append(match)

    return upcoming


def get_needs_action_matches(matches) -> list:
    """
    Return matches that currently require user attention.

    Includes:
        - matches awaiting scheduling
        - scheduled matches whose time has passed and
          still need a result

    Schedule proposals and result confirmations are
    handled separately by the Needs Action inbox.
    """

    now = datetime.now(timezone.utc)

    needs_action = []

    for match in matches:

        if match.status == "awaiting_schedule":
            needs_action.append(match)
            continue

        if (
            match.status == "scheduled"
            and match.scheduled_at
            and match.scheduled_at <= now
            and match.result_status == "not_submitted"
        ):
            needs_action.append(match)

    return needs_action


def get_completed_matches(matches) -> list:
    """Return completed matches."""

    return [
        match
        for match in matches
        if match.status == "completed"
    ]


def get_cancelled_matches(matches) -> list:
    """Return cancelled matches."""

    return [
        match
        for match in matches
        if match.status == "cancelled"
    ]



# ============================================================
# MY MATCHES MAIN MENU
# ============================================================


@router.message(F.text == MAIN_MENU_MY_MATCHES)
async def my_matches_handler(
    message: Message,
) -> None:
    """Open the My Matches navigation menu."""

    user = await get_user_by_telegram_id(
        message.from_user.id
    )

    if not user:
        await message.answer(
            profile_not_found_message()
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    upcoming = get_upcoming_matches(
        matches
    )

    needs_action_matches = get_needs_action_matches(
        matches
    )

    pending_schedule_requests = (
        await get_pending_schedule_requests(user.id)
    )

    needs_action_count = len(
        pending_schedule_requests
    )

    needs_action_count += len(
        needs_action_matches
    )

    needs_action_count += sum(
        1
        for match in matches
        if (
            match.status == "scheduled"
            and match.result_status == "pending_confirmation"
            and match.result_submitted_by_id != user.id
        )
    )

    completed = get_completed_matches(
        matches
    )

    cancelled = get_cancelled_matches(
        matches
    )

    my_matches_text = my_matches_message(
        upcoming_count=len(upcoming),
        needs_action_count=needs_action_count,
        completed_count=len(completed),
        cancelled_count=len(cancelled),
    )

    await message.answer(
        my_matches_text,
        reply_markup=get_my_matches_keyboard(),
    )






@router.callback_query(
    F.data.startswith("matches:confirm_result:")
)
async def confirm_result_handler(
    callback: CallbackQuery,
) -> None:
    """Confirm a submitted result and notify both players."""

    match_id = int(callback.data.split(":")[2])

    user = await get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer(
            "Profile not found.",
            show_alert=True,
        )
        return

    try:
        match = await confirm_match_result(
            match_id=match_id,
            confirmed_by_id=user.id,
        )
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    winner = (
        match.player_one
        if match.winner_id == match.player_one_id
        else match.player_two
    )
    loser = (
        match.player_two
        if match.winner_id == match.player_one_id
        else match.player_one
    )

    result_text = (
        "✅ RESULT CONFIRMED\n\n"
        f"🎾 Match #{match.id}\n\n"
        f"Set 1: {match.set_1_player_one_score}-"
        f"{match.set_1_player_two_score}\n"
        f"Set 2: {match.set_2_player_one_score}-"
        f"{match.set_2_player_two_score}"
    )

    if (
        match.set_3_player_one_score is not None
        and match.set_3_player_two_score is not None
    ):
        result_text += (
            f"\nSet 3: {match.set_3_player_one_score}-"
            f"{match.set_3_player_two_score}"
        )

    result_text += (
        "\n\n"
        f"🏆 Winner: {winner.first_name} {winner.last_name}\n"
        f"🎾 Loser: {loser.first_name} {loser.last_name}\n\n"
        "The match has been completed."
    )

    # Update the confirming player's existing message.
    await safe_edit_text(callback, result_text)
    await callback.answer("Result confirmed.")

    # Notify the other participant, regardless of who accepted
    # the original challenge or submitted the result.
    other_player = (
        match.player_two
        if match.player_one_id == user.id
        else match.player_one
    )

    try:
        await callback.bot.send_message(
            chat_id=other_player.telegram_id,
            text=result_text,
        )
    except Exception:
        logger.exception(
            "Could not notify the other player for match #%s",
            match.id,
        )



def parse_set_score(text: str) -> tuple[int, int]:
    """
    Parse a set score entered as Player 1:Player 2.

    Example:
        6:4
    """

    value = text.strip()
    parts = value.split(":")

    if len(parts) != 2:
        raise ValueError(
            "Please enter the score in this format: 6:4"
        )

    player_one_text = parts[0].strip()
    player_two_text = parts[1].strip()

    if not (
        player_one_text.isdigit()
        and player_two_text.isdigit()
    ):
        raise ValueError(
            "Scores must be numbers. Example: 6:4"
        )

    player_one_score = int(player_one_text)
    player_two_score = int(player_two_text)

    if player_one_score < 0 or player_two_score < 0:
        raise ValueError(
            "Scores cannot be negative."
        )

    return player_one_score, player_two_score


async def _validate_and_parse_set_score(
    message: Message,
) -> tuple[int, int] | None:
    """Parse and validate one tennis set score."""

    try:
        player_one_score, player_two_score = (
            parse_set_score(message.text or "")
        )
    except ValueError as error:
        await message.answer(
            score_parse_error_message(str(error))
        )
        return None

    from services.tennis_scoring import validate_set_score

    try:
        validate_set_score(
            player_one_score=player_one_score,
            player_two_score=player_two_score,
        )
    except ValueError as error:
        await message.answer(
            invalid_set_score_message(str(error))
        )
        return None

    return player_one_score, player_two_score


@router.callback_query(
    F.data.startswith("matches:submit_result:")
)
async def submit_result_handler(
    callback: CallbackQuery,
    state,
) -> None:
    """Start the Best-of-3 match result submission flow."""

    match_id = int(
        callback.data.split(":")[2]
    )

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Profile not found.",
            show_alert=True,
        )
        return

    match = await get_match_by_id(match_id)

    if not match:
        await callback.answer(
            "Match not found.",
            show_alert=True,
        )
        return

    if user.id not in (
        match.player_one_id,
        match.player_two_id,
    ):
        await callback.answer(
            "You are not a player in this match.",
            show_alert=True,
        )
        return

    if match.status != "scheduled":
        await callback.answer(
            "This match is not available for result submission.",
            show_alert=True,
        )
        return

    if match.result_status != "not_submitted":
        await callback.answer(
            "A result has already been submitted.",
            show_alert=True,
        )
        return

    if match.not_played_requested_by_id is not None:
        await callback.answer(
            "A not-played request is awaiting a response.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.update_data(
        match_id=match_id,
        submitted_by_id=user.id,
    )

    await state.set_state(
        MatchResultStates.waiting_for_set_1_score
    )

    await callback.message.answer(
        result_submission_message(match)
    )

    await callback.answer()


@router.message(
    MatchResultStates.waiting_for_set_1_score
)
async def set_1_score_handler(
    message: Message,
    state,
) -> None:
    """Receive and validate Set 1."""

    result = await _validate_and_parse_set_score(message)

    if result is None:
        return

    player_one_score, player_two_score = result

    await state.update_data(
        set_1_player_one_score=player_one_score,
        set_1_player_two_score=player_two_score,
    )

    await state.set_state(
        MatchResultStates.waiting_for_set_2_score
    )

    await message.answer(
        set_2_submission_message(
            player_one_score=player_one_score,
            player_two_score=player_two_score,
        )
    )


@router.message(
    MatchResultStates.waiting_for_set_2_score
)
async def set_2_score_handler(
    message: Message,
    state,
) -> None:
    """Receive and validate Set 2."""

    result = await _validate_and_parse_set_score(message)

    if result is None:
        return

    player_one_score, player_two_score = result

    data = await state.get_data()

    set_1_player_one_score = data.get(
        "set_1_player_one_score"
    )
    set_1_player_two_score = data.get(
        "set_1_player_two_score"
    )

    if (
        set_1_player_one_score is None
        or set_1_player_two_score is None
    ):
        await state.clear()

        await message.answer(
            result_session_expired_message()
        )
        return

    await state.update_data(
        set_2_player_one_score=player_one_score,
        set_2_player_two_score=player_two_score,
    )

    from services.tennis_scoring import get_match_winner

    try:
        match_winner = get_match_winner(
            set_1_player_one_score=set_1_player_one_score,
            set_1_player_two_score=set_1_player_two_score,
            set_2_player_one_score=player_one_score,
            set_2_player_two_score=player_two_score,
        )
    except ValueError as error:
        await message.answer(
            invalid_match_result_message(str(error))
        )
        return

    if match_winner is not None:
        await _finalize_result_submission(
            message=message,
            state=state,
        )
        return

    await state.set_state(
        MatchResultStates.waiting_for_set_3_score
    )

    await message.answer(
        set_3_submission_message(
            set_1_player_one_score=set_1_player_one_score,
            set_1_player_two_score=set_1_player_two_score,
            set_2_player_one_score=player_one_score,
            set_2_player_two_score=player_two_score,
        )
    )


@router.message(
    MatchResultStates.waiting_for_set_3_score
)
async def set_3_score_handler(
    message: Message,
    state,
) -> None:
    """Receive and validate Set 3."""

    result = await _validate_and_parse_set_score(message)

    if result is None:
        return

    player_one_score, player_two_score = result

    data = await state.get_data()

    set_1_player_one_score = data.get(
        "set_1_player_one_score"
    )
    set_1_player_two_score = data.get(
        "set_1_player_two_score"
    )
    set_2_player_one_score = data.get(
        "set_2_player_one_score"
    )
    set_2_player_two_score = data.get(
        "set_2_player_two_score"
    )

    if (
        set_1_player_one_score is None
        or set_1_player_two_score is None
        or set_2_player_one_score is None
        or set_2_player_two_score is None
    ):
        await state.clear()

        await message.answer(
            result_session_expired_message()
        )
        return

    await state.update_data(
        set_3_player_one_score=player_one_score,
        set_3_player_two_score=player_two_score,
    )

    await _finalize_result_submission(
        message=message,
        state=state,
    )


async def _finalize_result_submission(
    message: Message,
    state,
) -> None:
    """Submit the complete Best-of-3 result for confirmation."""

    data = await state.get_data()

    match_id = data.get("match_id")
    submitted_by_id = data.get("submitted_by_id")

    set_1_player_one_score = data.get(
        "set_1_player_one_score"
    )
    set_1_player_two_score = data.get(
        "set_1_player_two_score"
    )
    set_2_player_one_score = data.get(
        "set_2_player_one_score"
    )
    set_2_player_two_score = data.get(
        "set_2_player_two_score"
    )
    set_3_player_one_score = data.get(
        "set_3_player_one_score"
    )
    set_3_player_two_score = data.get(
        "set_3_player_two_score"
    )

    if (
        match_id is None
        or submitted_by_id is None
        or set_1_player_one_score is None
        or set_1_player_two_score is None
        or set_2_player_one_score is None
        or set_2_player_two_score is None
    ):
        await state.clear()

        await message.answer(
            result_session_expired_message()
        )
        return

    try:
        match = await submit_match_result(
            match_id=match_id,
            submitted_by_id=submitted_by_id,
            set_1_player_one_score=set_1_player_one_score,
            set_1_player_two_score=set_1_player_two_score,
            set_2_player_one_score=set_2_player_one_score,
            set_2_player_two_score=set_2_player_two_score,
            set_3_player_one_score=set_3_player_one_score,
            set_3_player_two_score=set_3_player_two_score,
        )
    except ValueError as error:
        await message.answer(
            str(error)
        )
        return

    await state.clear()

    await message.answer(
        submitted_result_message(
            match_id=match.id,
            set_1_player_one_score=set_1_player_one_score,
            set_1_player_two_score=set_1_player_two_score,
            set_2_player_one_score=set_2_player_one_score,
            set_2_player_two_score=set_2_player_two_score,
            set_3_player_one_score=set_3_player_one_score,
            set_3_player_two_score=set_3_player_two_score,
        )
    )

    submitter = (
        match.player_one
        if match.player_one_id == submitted_by_id
        else match.player_two
    )
    opponent = (
        match.player_two
        if match.player_one_id == submitted_by_id
        else match.player_one
    )

    score_lines = [
        (
            f"Set 1: {set_1_player_one_score}–"
            f"{set_1_player_two_score}"
        ),
        (
            f"Set 2: {set_2_player_one_score}–"
            f"{set_2_player_two_score}"
        ),
    ]

    if (
        set_3_player_one_score is not None
        and set_3_player_two_score is not None
    ):
        score_lines.append(
            f"Set 3: {set_3_player_one_score}–"
            f"{set_3_player_two_score}"
        )

    notification_text = (
        f"🎾 Match #{match.id}\n\n"
        f"{submitter.first_name} {submitter.last_name} "
        "submitted the result.\n\n"
        + "\n".join(score_lines)
        + "\n\nPlease confirm the result:"
    )

    try:
        await message.bot.send_message(
            chat_id=opponent.telegram_id,
            text=notification_text,
            reply_markup=get_result_actions_keyboard(
                match.id,
                match.result_status,
                can_confirm=True,
            ),
        )
    except Exception:
        logger.warning(
            "Could not notify Telegram user %s about submitted result for match %s",
            opponent.telegram_id,
            match.id,
            exc_info=True,
        )


@router.callback_query(
    F.data == "matches:back"
)
async def matches_back_handler(
    callback: CallbackQuery,
) -> None:
    """Return to the main My Matches navigation menu."""

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message()
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    upcoming = get_upcoming_matches(
        matches
    )

    needs_action_matches = get_needs_action_matches(
        matches
    )

    pending_schedule_requests = (
        await get_pending_schedule_requests(user.id)
    )

    needs_action_count = len(
        pending_schedule_requests
    )

    needs_action_count += len(
        needs_action_matches
    )

    needs_action_count += sum(
        1
        for match in matches
        if (
            match.status == "scheduled"
            and match.result_status == "pending_confirmation"
            and match.result_submitted_by_id != user.id
        )
    )

    completed = get_completed_matches(
        matches
    )

    cancelled = get_cancelled_matches(
        matches
    )

    my_matches_text = my_matches_message(
        upcoming_count=len(upcoming),
        needs_action_count=needs_action_count,
        completed_count=len(completed),
        cancelled_count=len(cancelled),
    )

    await safe_edit_text(
        callback,
        my_matches_text,
        reply_markup=get_my_matches_keyboard(),
    )

    await callback.answer()



# ============================================================
# UPCOMING
# ============================================================


def _get_upcoming_date_groups(matches):
    """Group scheduled upcoming matches by calendar date."""

    groups: dict = {}

    for match in matches:
        if not match.scheduled_at:
            continue

        match_date = match.scheduled_at.date()
        groups.setdefault(match_date, []).append(match)

    return dict(sorted(groups.items()))


def _upcoming_date_title(match_date, today):
    """Return a friendly title for an upcoming calendar date."""

    if match_date == today:
        return "Today"

    if match_date == today + timedelta(days=1):
        return "Tomorrow"

    return match_date.strftime("%B %-d")


def _get_upcoming_page(
    scheduled_matches,
    start_index: int,
) -> tuple[list, int, bool]:
    """
    Build one upcoming page.

    The page targets four matches, but never cuts the first
    date group. Later date groups may be split across pages
    when necessary to keep the page compact.
    """

    if start_index >= len(scheduled_matches):
        return [], start_index, False

    first_match = scheduled_matches[start_index]
    first_date = first_match.scheduled_at.date()

    end_index = start_index

    # Always include the complete first date group.
    while (
        end_index < len(scheduled_matches)
        and scheduled_matches[end_index].scheduled_at.date()
        == first_date
    ):
        end_index += 1

    first_date_count = end_index - start_index

    # If the first date already fills/exceeds the page target,
    # stop here. We never split the first date group.
    if first_date_count >= 4:
        has_next = end_index < len(scheduled_matches)
        return (
            scheduled_matches[start_index:end_index],
            end_index,
            has_next,
        )

    # Fill the remaining space from later dates.
    target_end = start_index + 4

    while end_index < len(scheduled_matches) and end_index < target_end:
        end_index += 1

    has_next = end_index < len(scheduled_matches)

    return (
        scheduled_matches[start_index:end_index],
        end_index,
        has_next,
    )


def _get_previous_upcoming_index(
    scheduled_matches,
    current_index: int,
) -> int | None:
    """Return the starting index of the previous upcoming page."""

    if current_index <= 0:
        return None

    previous_index = 0

    while previous_index < current_index:
        _, next_index, has_next = _get_upcoming_page(
            scheduled_matches,
            previous_index,
        )

        if not has_next or next_index is None:
            break

        if next_index >= current_index:
            return previous_index

        previous_index = next_index

    return None


def _build_upcoming_message(
    upcoming,
    user_id: int,
    start_index: int,
) -> tuple[str, int | None, bool, list]:
    """Build one page of the upcoming match timeline."""

    today = datetime.now().date()

    scheduled = sorted(
        (
            match
            for match in upcoming
            if match.scheduled_at
        ),
        key=lambda match: match.scheduled_at,
    )

    unscheduled = [
        match
        for match in upcoming
        if not match.scheduled_at
    ]

    if not scheduled:
        message_parts = []

        for match in unscheduled:
            message_parts.append(
                format_upcoming_match_summary(
                    match,
                    user_id,
                )
            )
            message_parts.append("")

        return (
            "\n".join(message_parts).rstrip(),
            None,
            False,
            unscheduled,
        )

    page_matches, next_start, has_next = _get_upcoming_page(
        scheduled,
        start_index,
    )

    message_parts = ["🎟️ Upcoming"]
    message_parts.append("")
    current_date = None

    for match in page_matches:
        match_date = match.scheduled_at.date()

        if match_date != current_date:
            if current_date is not None:
                message_parts.append("")

            message_parts.append(
                _upcoming_date_title(
                    match_date,
                    today,
                )
            )
            message_parts.append("")

            current_date = match_date

        message_parts.append(
            format_upcoming_match_summary(
                match,
                user_id,
            )
        )
        message_parts.append("")

    # Unscheduled matches belong at the very end of the
    # scheduled timeline, never in the middle of dated matches.
    if not has_next and unscheduled:
        for match in unscheduled:
            message_parts.append(
                format_upcoming_match_summary(
                    match,
                    user_id,
                )
            )
            message_parts.append("")

    next_index = next_start if has_next else None

    visible_matches = list(page_matches)

    if not has_next:
        visible_matches.extend(unscheduled)

    return (
        "\n".join(message_parts).rstrip(),
        next_index,
        has_next,
        visible_matches,
    )


@router.callback_query(
    F.data == "matches:upcoming"
)
async def upcoming_matches_handler(
    callback: CallbackQuery,
) -> None:
    """Show the first page of upcoming matches."""

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    upcoming = get_upcoming_matches(
        matches
    )

    if not upcoming:
        await safe_edit_text(
            callback,
            match_empty_message("upcoming"),
            reply_markup=get_my_matches_keyboard(),
        )

        await callback.answer()
        return

    (
        message,
        next_index,
        has_next,
        visible_matches,
    ) = _build_upcoming_message(
        upcoming,
        user.id,
        0,
    )

    await safe_edit_text(
        callback,
        message,
        reply_markup=get_upcoming_matches_keyboard(
            visible_matches=visible_matches,
            previous_index=None,
            next_index=next_index,
            current_index=0,
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("matches:upcoming:next:")
)
async def upcoming_matches_next_handler(
    callback: CallbackQuery,
) -> None:
    """Show the next page of upcoming matches."""

    parts = callback.data.split(":")

    current_index = int(parts[-2])
    next_index = int(parts[-1])

    if current_index < 0 or next_index < 0:
        await callback.answer()
        return

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    upcoming = get_upcoming_matches(
        matches
    )

    (
        message,
        next_page_index,
        has_next,
        visible_matches,
    ) = _build_upcoming_message(
        upcoming,
        user.id,
        next_index,
    )

    scheduled = sorted(
        (
            match
            for match in upcoming
            if match.scheduled_at
        ),
        key=lambda match: match.scheduled_at,
    )

    previous_index = _get_previous_upcoming_index(
        scheduled,
        next_index,
    )

    await safe_edit_text(
        callback,
        message,
        reply_markup=get_upcoming_matches_keyboard(
            visible_matches=visible_matches,
            previous_index=previous_index,
            next_index=next_page_index,
            current_index=next_index,
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("matches:upcoming:previous:")
)
async def upcoming_matches_previous_handler(
    callback: CallbackQuery,
) -> None:
    """Return to the previous page of upcoming matches."""

    previous_index = int(
        callback.data.rsplit(":", 1)[1]
    )

    if previous_index < 0:
        await callback.answer()
        return

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    upcoming = get_upcoming_matches(
        matches
    )

    (
        message,
        next_page_index,
        has_next,
        visible_matches,
    ) = _build_upcoming_message(
        upcoming,
        user.id,
        previous_index,
    )

    scheduled = sorted(
        (
            match
            for match in upcoming
            if match.scheduled_at
        ),
        key=lambda match: match.scheduled_at,
    )

    earlier_index = _get_previous_upcoming_index(
        scheduled,
        previous_index,
    )

    await safe_edit_text(
        callback,
        message,
        reply_markup=get_upcoming_matches_keyboard(
            visible_matches=visible_matches,
            previous_index=earlier_index,
            next_index=next_page_index,
            current_index=previous_index,
        ),
    )

    await callback.answer()


# ============================================================
# NEEDS ACTION
# ============================================================


@router.callback_query(
    F.data == "matches:needs_action"
)
async def needs_action_matches_handler(
    callback: CallbackQuery,
) -> None:
    """Show the user's Needs Action inbox."""

    await _show_needs_action_page(
        callback=callback,
        page=0,
    )


@router.callback_query(
    F.data.startswith("matches:needs_action:page:")
)
async def needs_action_page_handler(
    callback: CallbackQuery,
) -> None:
    """Show a page of Needs Action items."""

    page = int(callback.data.rsplit(":", 1)[1])

    if page < 0:
        await callback.answer()
        return

    await _show_needs_action_page(
        callback=callback,
        page=page,
    )


async def _show_needs_action_page(
    callback: CallbackQuery,
    page: int,
) -> None:
    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    pending_schedule_requests = (
        await get_pending_schedule_requests(user.id)
    )

    needs_action_matches = get_needs_action_matches(
        matches
    )

    now = datetime.now(timezone.utc)

    action_items = []

    for request in pending_schedule_requests:
        action_items.append(
            (
                request.created_at,
                "schedule_proposal",
                request,
            )
        )

    for match in needs_action_matches:
        if match.status == "awaiting_schedule":
            action_items.append(
                (
                    match.created_at,
                    "schedule",
                    match,
                )
            )
            continue

        if (
            match.status == "scheduled"
            and match.not_played_requested_by_id is not None
        ):
            action_items.append(
                (
                    match.not_played_requested_at or match.scheduled_at or match.created_at,
                    "not_played_pending",
                    match,
                )
            )
            continue

        scheduled_at = match.scheduled_at
        if scheduled_at and scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        if (
            match.status == "scheduled"
            and scheduled_at
            and scheduled_at <= now
            and match.result_status == "not_submitted"
            and match.result_submitted_by_id is None
        ):
            action_items.append(
                (
                    scheduled_at,
                    "result",
                    match,
                )
            )

    for match in matches:
        if (
            match.status == "scheduled"
            and match.result_status == "pending_confirmation"
            and match.result_submitted_by_id != user.id
        ):
            action_items.append(
                (
                    match.updated_at,
                    "confirmation",
                    match,
                )
            )

    action_items.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    if not action_items:
        await safe_edit_text(
            callback,
            match_empty_message("needs_action"),
            reply_markup=get_my_matches_keyboard(),
        )

        await callback.answer()
        return

    page_size = 4
    start_index = page * page_size
    end_index = start_index + page_size

    if start_index >= len(action_items):
        await callback.answer(
            "No more actions available."
        )
        return

    page_items = action_items[start_index:end_index]
    has_older = end_index < len(action_items)

    message_parts = [
        needs_action_header(len(action_items)),
        "",
    ]

    keyboard_rows = []

    for _, action_type, item in page_items:

        if action_type == "schedule":
            message_parts.append(
                format_needs_action_schedule(
                    item,
                    user.id,
                )
            )

            keyboard = get_needs_action_keyboard(
                action_type="schedule",
                match_id=item.id,
            )

        elif action_type == "schedule_proposal":
            message_parts.append(
                format_needs_action_schedule_proposal(
                    item,
                    user.id,
                )
            )

            keyboard = get_needs_action_keyboard(
                action_type="schedule_proposal",
                match_id=item.match.id,
                request_id=item.id,
            )

        elif action_type == "result":
            message_parts.append(
                format_needs_action_result(
                    item,
                    user.id,
                )
            )

            keyboard = get_needs_action_keyboard(
                action_type="result",
                match_id=item.id,
            )

        elif action_type == "not_played_pending":
            message_parts.append(
                format_needs_action_not_played(
                    item,
                    user.id,
                )
            )

            if item.not_played_requested_by_id == user.id:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            else:
                keyboard = get_needs_action_keyboard(
                    action_type="not_played_pending",
                    match_id=item.id,
                )

        elif action_type == "confirmation":
            message_parts.append(
                format_needs_action_confirmation(
                    item,
                    user.id,
                )
            )

            keyboard = get_needs_action_keyboard(
                action_type="confirmation",
                match_id=item.id,
            )

        else:
            continue

        message_parts.append("")

        keyboard_rows.extend(keyboard.inline_keyboard)

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="← Previous",
                callback_data=f"matches:needs_action:page:{page - 1}",
            )
        )

    if has_older:
        navigation.append(
            InlineKeyboardButton(
                text="Next →",
                callback_data=f"matches:needs_action:page:{page + 1}",
            )
        )

    if navigation:
        keyboard_rows.append(navigation)

    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="Back",
                callback_data="matches:back",
            )
        ]
    )

    await safe_edit_text(
        callback,
        "\n".join(message_parts).rstrip(),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard_rows
        ),
    )

    await callback.answer()


# ============================================================
# MATCH NOT-PLAYED REQUESTS
# ============================================================


@router.callback_query(F.data.startswith("matches:not_played:request:"))
async def request_match_not_played_handler(
    callback: CallbackQuery,
) -> None:
    """Ask the opponent to confirm that a scheduled match was not played."""

    try:
        match_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Invalid match request.", show_alert=True)
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(profile_not_found_message(), show_alert=True)
        return

    try:
        match = await request_match_not_played(match_id, user.id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    requester = (
        match.player_one
        if match.player_one_id == user.id
        else match.player_two
    )
    opponent = (
        match.player_two
        if match.player_one_id == user.id
        else match.player_one
    )

    scheduled_text = (
        match.scheduled_at.strftime("%b %d, %H:%M")
        if match.scheduled_at
        else "time not set"
    )

    try:
        await callback.bot.send_message(
            chat_id=opponent.telegram_id,
            text=(
                f"Match #{match.id}: Please respond\n\n"
                f"{requester.first_name} {requester.last_name} says "
                "this match wasn't played.\n"
                f"Scheduled: {scheduled_text}\n\n"
                "Please confirm the match wasn't played:"
            ),
            reply_markup=get_needs_action_keyboard(
                action_type="not_played_pending",
                match_id=match.id,
            ),
        )
    except Exception:
        logger.warning(
            "Could not notify Telegram user %s about not-played request for match %s",
            opponent.telegram_id,
            match.id,
            exc_info=True,
        )

    await safe_edit_text(
        callback,
        f"Not Played request sent for Match #{match.id}.\n\n"
        "Waiting for your opponent to respond.",
        reply_markup=get_schedule_accepted_keyboard(),
    )
    await callback.answer("Request sent.")


@router.callback_query(F.data.startswith("matches:not_played:confirm:"))
async def confirm_match_not_played_handler(
    callback: CallbackQuery,
) -> None:
    """Confirm the opponent's not-played request."""

    try:
        match_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Invalid match request.", show_alert=True)
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(profile_not_found_message(), show_alert=True)
        return

    try:
        match = await confirm_match_not_played(match_id, user.id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    text = (
        f"Match #{match.id} was marked as not played and cancelled.\n\n"
        f"{match.player_one.first_name} {match.player_one.last_name} "
        f"vs {match.player_two.first_name} {match.player_two.last_name}\n\n"
        "No result or ranking points were recorded."
    )

    await safe_edit_text(
        callback,
        text,
        reply_markup=get_schedule_accepted_keyboard(),
    )

    for player in (match.player_one, match.player_two):
        if player.telegram_id == callback.from_user.id:
            continue
        try:
            await callback.bot.send_message(
                chat_id=player.telegram_id,
                text=text,
                reply_markup=get_schedule_accepted_keyboard(),
            )
        except Exception:
            logger.warning(
                "Could not notify Telegram user %s about not-played confirmation for match %s",
                player.telegram_id,
                match.id,
                exc_info=True,
            )

    await callback.answer("Match cancelled.")


@router.callback_query(F.data.startswith("matches:not_played:reject:"))
async def reject_match_not_played_handler(
    callback: CallbackQuery,
) -> None:
    """Reject the opponent's not-played request."""

    try:
        match_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Invalid match request.", show_alert=True)
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(profile_not_found_message(), show_alert=True)
        return

    try:
        match = await reject_match_not_played(match_id, user.id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    # Both players are told the request was rejected.
    text = (
        f"The not-played request for match #{match.id} was rejected.\n\n"
        "The match remains scheduled. If you played, submit the result in My Matches."
    )

    await safe_edit_text(
        callback,
        text,
        reply_markup=get_schedule_accepted_keyboard(),
    )

    for player in (match.player_one, match.player_two):
        if player.telegram_id == callback.from_user.id:
            continue
        try:
            await callback.bot.send_message(
                chat_id=player.telegram_id,
                text=text,
                reply_markup=get_schedule_accepted_keyboard(),
            )
        except Exception:
            logger.warning(
                "Could not notify Telegram user %s about rejected not-played request for match %s",
                player.telegram_id,
                match.id,
                exc_info=True,
            )

    await callback.answer("Request rejected.")


# ============================================================
# COMPLETED
# ============================================================


@router.callback_query(
    F.data == "matches:completed"
)
async def completed_matches_handler(
    callback: CallbackQuery,
) -> None:
    """Show completed matches, four per page."""

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    completed = get_completed_matches(
        matches
    )

    if not completed:
        await safe_edit_text(
            callback,
            match_empty_message("completed"),
            reply_markup=get_my_matches_keyboard(),
        )

        await callback.answer()
        return

    completed.sort(
        key=lambda match: match.played_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    page_size = 4
    page = 0

    start_index = page * page_size
    end_index = start_index + page_size

    page_matches = completed[start_index:end_index]
    has_older = end_index < len(completed)

    message_parts = [
        "🗃️ Completed",
        "",
    ]

    for match in page_matches:
        message_parts.append(
            format_match_summary(
                match,
                user.id,
            )
        )
        message_parts.append("")

    await safe_edit_text(
        callback,
        "\n".join(message_parts).rstrip(),
        reply_markup=get_completed_matches_keyboard(
            page=page,
            has_older=has_older,
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("matches:completed:page:")
)
async def completed_matches_page_handler(
    callback: CallbackQuery,
) -> None:
    """Show a page of completed match history."""

    page = int(callback.data.rsplit(":", 1)[1])

    if page < 0:
        await callback.answer()
        return

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    completed = get_completed_matches(
        matches
    )

    completed.sort(
        key=lambda match: match.played_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    page_size = 4
    start_index = page * page_size
    end_index = start_index + page_size

    if start_index >= len(completed):
        await callback.answer(
            "No older matches available."
        )
        return

    page_matches = completed[start_index:end_index]
    has_older = end_index < len(completed)

    message_parts = [
        "🗃️ Completed",
        "",
    ]

    for match in page_matches:
        message_parts.append(
            format_match_summary(
                match,
                user.id,
            )
        )
        message_parts.append("")

    await safe_edit_text(
        callback,
        "\n".join(message_parts).rstrip(),
        reply_markup=get_completed_matches_keyboard(
            page=page,
            has_older=has_older,
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data == "matches:cancelled"
)
async def cancelled_matches_handler(
    callback: CallbackQuery,
) -> None:
    """Show cancelled matches, four per page."""

    await _show_cancelled_page(
        callback=callback,
        page=0,
    )


@router.callback_query(
    F.data.startswith("matches:cancelled:page:")
)
async def cancelled_matches_page_handler(
    callback: CallbackQuery,
) -> None:
    """Show a page of cancelled matches."""

    page = int(callback.data.rsplit(":", 1)[1])

    if page < 0:
        await callback.answer()
        return

    await _show_cancelled_page(
        callback=callback,
        page=page,
    )


# ============================================================
# CANCELLED
# ============================================================


async def _show_cancelled_page(
    callback: CallbackQuery,
    page: int,
) -> None:
    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    matches = await get_matches_for_user(
        user.id
    )

    cancelled = get_cancelled_matches(
        matches
    )

    if not cancelled:
        await safe_edit_text(
            callback,
            match_empty_message("cancelled"),
            reply_markup=get_my_matches_keyboard(),
        )

        await callback.answer()
        return

    page_size = 4
    start_index = page * page_size
    end_index = start_index + page_size

    if start_index >= len(cancelled):
        await callback.answer(
            "No more cancelled matches available."
        )
        return

    page_matches = cancelled[start_index:end_index]
    has_older = end_index < len(cancelled)

    await safe_edit_text(
        callback,
        format_cancelled_matches_message(
            matches=page_matches,
            user_id=user.id,
        ),
        reply_markup=get_cancelled_matches_keyboard(
            page=page,
            has_older=has_older,
        ),
    )

    await callback.answer()


# ============================================================
# VIEW INDIVIDUAL MATCH
# ============================================================


@router.callback_query(
    F.data.startswith("matches:view:")
)
async def view_match_handler(
    callback: CallbackQuery,
) -> None:
    """Open an individual match."""

    parts = callback.data.split(":")

    section = parts[2]
    match_id = int(parts[3])

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            profile_not_found_message(),
            show_alert=True,
        )
        return

    match = await get_match_by_id(
        match_id
    )

    if not match:
        await callback.answer(
            match_not_found_message(),
            show_alert=True,
        )
        return

    if user.id not in (
        match.player_one_id,
        match.player_two_id,
    ):
        await callback.answer(
            not_match_player_message(),
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # UPCOMING MATCH DETAIL
    # --------------------------------------------------------

    if section == "upcoming":
        opponent = (
            match.player_two
            if match.player_one_id == user.id
            else match.player_one
        )

        opponent_rank, _ = await get_player_rank(
            opponent.id
        )

        opponent_streak, _ = await get_player_match_stats(
            opponent.id
        )

        await safe_edit_text(
            callback,
            format_upcoming_match_detail(
                match=match,
                user_id=user.id,
                opponent_rank=opponent_rank,
                opponent_streak=opponent_streak,
            ),
            reply_markup=get_match_navigation_keyboard(
                match_id=match.id,
                section=section,
                status=match.status,
            ),
        )

        await callback.answer()
        return

    # --------------------------------------------------------
    # NEEDS ACTION RESULT VIEW
    # --------------------------------------------------------

    if section == "needs_action":

        if match.status == "awaiting_schedule":
            reply_markup = get_match_navigation_keyboard(
                match_id=match.id,
                section=section,
                status=match.status,
            )

        else:
            can_confirm = (
                match.result_status == "pending_confirmation"
                and match.result_submitted_by_id != user.id
            )

            result_actions = get_result_actions_keyboard(
                match_id=match.id,
                result_status=match.result_status,
                can_confirm=can_confirm,
            )

            result_actions.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Back",
                        callback_data="matches:needs_action",
                    )
                ]
            )

            reply_markup = result_actions

        await safe_edit_text(
            callback,
            format_match_message(
                match=match,
                user_id=user.id,
            ),
            reply_markup=reply_markup,
        )

        await callback.answer()
        return

# ============================================================
# MATCH CANCELLATION
# ============================================================


@router.callback_query(
    F.data.startswith("matches:cancel:")
)
async def cancel_match_prompt_handler(
    callback: CallbackQuery,
) -> None:
    """Ask the player to confirm match cancellation."""

    parts = callback.data.split(":")
    section = parts[2] if len(parts) == 4 else None
    match_id = int(parts[-1])

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(profile_not_found_message(), show_alert=True)
        return

    match = await get_match_by_id(match_id)
    if not match:
        await callback.answer(match_not_found_message(), show_alert=True)
        return

    if user.id not in (match.player_one_id, match.player_two_id):
        await callback.answer(not_match_player_message(), show_alert=True)
        return

    if match.status not in ("awaiting_schedule", "scheduled"):
        await callback.answer(
            "This match can no longer be cancelled.",
            show_alert=True,
        )
        return

    section = section or (
        "upcoming" if match.status == "scheduled" else "needs_action"
    )

    await safe_edit_text(
        callback,
        f"Cancel match #{match.id}?\n\n"
        f"{match.player_one.first_name} {match.player_one.last_name} "
        f"vs {match.player_two.first_name} {match.player_two.last_name}\n\n"
        "This action cannot be undone.",
        reply_markup=get_cancel_confirmation_keyboard(
            match_id=match.id,
            section=section,
        ),
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("matches:confirm_cancel:")
)
async def confirm_cancel_match_handler(
    callback: CallbackQuery,
) -> None:
    """Cancel a match after explicit confirmation."""

    parts = callback.data.split(":")
    if len(parts) == 4:
        section = parts[2]
        raw_match_id = parts[3]
    elif len(parts) == 3:
        # Compatibility with older Telegram buttons.
        section = None
        raw_match_id = parts[2]
    else:
        await callback.answer(
            "Invalid cancellation button.",
            show_alert=True,
        )
        return

    match_id = int(raw_match_id)

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(profile_not_found_message(), show_alert=True)
        return

    match = await get_match_by_id(match_id)
    if not match:
        await callback.answer(match_not_found_message(), show_alert=True)
        return

    if user.id not in (match.player_one_id, match.player_two_id):
        await callback.answer(not_match_player_message(), show_alert=True)
        return

    section = section or (
        "upcoming" if match.status == "scheduled" else "needs_action"
    )

    try:
        match = await cancel_match(match_id=match_id, user_id=user.id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    await safe_edit_text(
        callback,
        f"🚫 Match #{match.id} cancelled.\n\n"
        f"{match.player_one.first_name} {match.player_one.last_name} "
        f"vs {match.player_two.first_name} {match.player_two.last_name}",
        reply_markup=get_schedule_accepted_keyboard(),
    )

    for player in (match.player_one, match.player_two):
        try:
            await callback.bot.send_message(
                chat_id=player.telegram_id,
                text=(
                    f"🚫 Match #{match.id} has been cancelled.\n\n"
                    f"{match.player_one.first_name} {match.player_one.last_name} "
                    f"vs {match.player_two.first_name} {match.player_two.last_name}"
                ),
                reply_markup=get_schedule_accepted_keyboard(),
            )
        except Exception:
            # The cancellation is committed; log notification failures.
            logger.warning(
                "Could not notify Telegram user %s about cancelled match %s",
                player.telegram_id,
                match.id,
                exc_info=True,
            )

    await callback.answer("Match cancelled.")


@router.callback_query(
    F.data.startswith("matches:keep:")
)
async def keep_match_handler(
    callback: CallbackQuery,
) -> None:
    """Dismiss cancellation confirmation and return to the match."""

    parts = callback.data.split(":")
    if len(parts) == 4:
        section = parts[2]
        raw_match_id = parts[3]
    elif len(parts) == 3:
        # Compatibility with older Telegram buttons.
        section = None
        raw_match_id = parts[2]
    else:
        await callback.answer(
            "Invalid cancellation button.",
            show_alert=True,
        )
        return

    match_id = int(raw_match_id)

    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(profile_not_found_message(), show_alert=True)
        return

    match = await get_match_by_id(match_id)
    if not match:
        await callback.answer(match_not_found_message(), show_alert=True)
        return

    if user.id not in (match.player_one_id, match.player_two_id):
        await callback.answer(not_match_player_message(), show_alert=True)
        return

    section = section or (
        "upcoming" if match.status == "scheduled" else "needs_action"
    )

    if section == "upcoming" and match.status == "scheduled":
        opponent = (
            match.player_two if match.player_one_id == user.id
            else match.player_one
        )
        opponent_rank, _ = await get_player_rank(opponent.id)
        opponent_streak, _ = await get_player_match_stats(opponent.id)
        text = format_upcoming_match_detail(
            match=match,
            user_id=user.id,
            opponent_rank=opponent_rank,
            opponent_streak=opponent_streak,
        )
    else:
        section = "needs_action"
        text = format_match_message(match=match, user_id=user.id)

    await safe_edit_text(
        callback,
        text,
        reply_markup=get_match_navigation_keyboard(
            match_id=match.id,
            section=section,
            status=match.status,
        ),
    )
    await callback.answer("Match kept.")
