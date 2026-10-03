from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.scheduling import (
    get_schedule_request_keyboard,
)
from bot.states.scheduling import SchedulingStates
from bot.ui.messages.common import (
    profile_not_found_message,
)
from bot.ui.messages.scheduling import (
    change_match_time_message,
    choose_time_message,
    invalid_date_format_message,
    invalid_time_format_message,
    match_scheduled_message,
    schedule_change_accepted_message,
    schedule_change_rejected_message,
    schedule_change_request_message,
    schedule_change_sent_message,
    schedule_match_message,
    schedule_request_message,
    schedule_request_rejected_message,
    schedule_request_sent_message,
)
from services.matches import (
    accept_schedule_request,
    create_schedule_change_request,
    create_schedule_request,
    get_schedule_request_by_id,
    reject_schedule_request,
)
from services.users import get_user_by_telegram_id


router = Router()

TASHKENT_TIMEZONE = ZoneInfo("Asia/Tashkent")


# ============================================================
# START SCHEDULING
# ============================================================


@router.callback_query(
    F.data.startswith("matches:propose_schedule:")
    | F.data.startswith("matches:change_schedule:")
)
async def start_scheduling_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Start the scheduling process.

    Supports both:
        - initial scheduling
        - changing an existing scheduled time
    """

    parts = callback.data.split(":")

    action = parts[1]
    match_id = int(parts[2])

    is_change = action == "change_schedule"

    await state.update_data(
        match_id=match_id,
        is_change=is_change,
    )

    await state.set_state(
        SchedulingStates.date
    )

    await callback.answer()

    if is_change:
        await callback.message.answer(
            change_match_time_message()
        )
    else:
        await callback.message.answer(
            schedule_match_message()
        )


# ============================================================
# DATE
# ============================================================


@router.message(
    SchedulingStates.date
)
async def scheduling_date_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Receive and validate the proposed date.
    """

    if not message.text:
        await message.answer(
            "Please enter the date as text.\n\n"
            "Example: 2026-10-10"
        )
        return

    date_text = message.text.strip()

    try:
        proposed_date = datetime.strptime(
            date_text,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        await message.answer(
            invalid_date_format_message()
        )
        return

    await state.update_data(
        proposed_date=proposed_date.isoformat(),
    )

    await state.set_state(
        SchedulingStates.time
    )

    await message.answer(
        choose_time_message()
    )


# ============================================================
# TIME
# ============================================================


@router.message(
    SchedulingStates.time
)
async def scheduling_time_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Receive and validate the proposed time.

    Once valid, create the appropriate schedule request
    and notify the opponent.
    """

    if not message.text:
        await message.answer(
            "Please enter the time as text.\n\n"
            "Example: 18:30"
        )
        return

    time_text = message.text.strip()

    try:
        proposed_time = datetime.strptime(
            time_text,
            "%H:%M",
        ).time()

    except ValueError:
        await message.answer(
            invalid_time_format_message()
        )
        return

    data = await state.get_data()

    match_id = data.get("match_id")
    proposed_date = data.get("proposed_date")
    is_change = data.get("is_change", False)

    if not match_id or not proposed_date:
        await state.clear()

        await message.answer(
            "Something went wrong with the "
            "scheduling process.\n\n"
            "Please try again."
        )
        return

    proposed_datetime = datetime.strptime(
        f"{proposed_date} {proposed_time:%H:%M}",
        "%Y-%m-%d %H:%M",
    ).replace(
        tzinfo=TASHKENT_TIMEZONE,
    )

    # ========================================================
    # GET DATABASE USER
    # ========================================================

    user = await get_user_by_telegram_id(
        message.from_user.id
    )

    if not user:
        await state.clear()

        await message.answer(
            profile_not_found_message()
        )
        return

    # ========================================================
    # CREATE REQUEST
    # ========================================================

    try:
        if is_change:
            schedule_request = (
                await create_schedule_change_request(
                    match_id=match_id,
                    requested_by_id=user.id,
                    proposed_at=proposed_datetime,
                )
            )
        else:
            schedule_request = await create_schedule_request(
                match_id=match_id,
                requested_by_id=user.id,
                proposed_at=proposed_datetime,
            )

    except ValueError as error:
        await state.clear()

        await message.answer(
            f"{error}"
        )
        return

    # ========================================================
    # LOAD REQUEST DETAILS
    # ========================================================

    schedule_request = await get_schedule_request_by_id(
        schedule_request.id
    )

    if not schedule_request:
        await state.clear()

        await message.answer(
            "Schedule request was created, but "
            "its details could not be loaded."
        )
        return

    opponent = schedule_request.recipient
    requester = schedule_request.requested_by

    # ========================================================
    # CLEAR FSM
    # ========================================================

    await state.clear()

    # ========================================================
    # CONFIRM TO REQUESTER
    # ========================================================

    if is_change:
        requester_text = schedule_change_sent_message(
            scheduled_at=proposed_datetime,
            opponent=opponent,
        )
    else:
        requester_text = schedule_request_sent_message(
            scheduled_at=proposed_datetime,
            opponent=opponent,
        )

    await message.answer(
        requester_text
    )

    # ========================================================
    # NOTIFY OPPONENT
    # ========================================================

    if is_change:
        opponent_text = schedule_change_request_message(
            requester=requester,
            scheduled_at=proposed_datetime,
        )
    else:
        opponent_text = schedule_request_message(
            requester=requester,
            scheduled_at=proposed_datetime,
        )

    await message.bot.send_message(
        chat_id=opponent.telegram_id,
        text=opponent_text,
        reply_markup=get_schedule_request_keyboard(
            schedule_request.id
        ),
    )


# ============================================================
# ACCEPT SCHEDULE REQUEST
# ============================================================


@router.callback_query(
    F.data.startswith("scheduling:accept:")
)
async def accept_schedule_handler(
    callback: CallbackQuery,
) -> None:
    """
    Accept a pending schedule request.

    Works for both:
        - initial scheduling
        - changing an existing schedule
    """

    request_id = int(
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

    # ========================================================
    # LOAD REQUEST BEFORE ACCEPTING
    # ========================================================

    pending_request = await get_schedule_request_by_id(
        request_id
    )

    if not pending_request:
        await callback.answer(
            "Schedule request not found.",
            show_alert=True,
        )
        return

    if pending_request.recipient_id != user.id:
        await callback.answer(
            "This request is not for you.",
            show_alert=True,
        )
        return

    match_before = pending_request.match

    was_schedule_change = (
        match_before.status == "scheduled"
    )

    # ========================================================
    # ACCEPT REQUEST
    # ========================================================

    try:
        schedule_request = await accept_schedule_request(
            request_id=request_id,
            user_id=user.id,
        )

    except ValueError as error:
        await callback.answer(
            str(error),
            show_alert=True,
        )
        return

    match = schedule_request.match
    requester = schedule_request.requested_by
    recipient = schedule_request.recipient

    scheduled_at = match.scheduled_at

    # ========================================================
    # REQUESTER NOTIFICATION
    # ========================================================

    if was_schedule_change:
        requester_text = schedule_change_accepted_message(
            scheduled_at=scheduled_at,
        )
    else:
        requester_text = match_scheduled_message(
            requester=recipient,
            scheduled_at=scheduled_at,
        )

    await callback.bot.send_message(
        chat_id=requester.telegram_id,
        text=requester_text,
    )

    # ========================================================
    # RECIPIENT CONFIRMATION
    # ========================================================

    if was_schedule_change:
        recipient_text = schedule_change_accepted_message(
            scheduled_at=scheduled_at,
        )
    else:
        recipient_text = match_scheduled_message(
            requester=requester,
            scheduled_at=scheduled_at,
        )

    await callback.message.edit_text(
        recipient_text
    )

    await callback.answer()


# ============================================================
# REJECT SCHEDULE REQUEST
# ============================================================


@router.callback_query(
    F.data.startswith("scheduling:reject:")
)
async def reject_schedule_handler(
    callback: CallbackQuery,
) -> None:
    """
    Reject a pending schedule request.

    If this was a schedule change, the existing match time
    remains unchanged.
    """

    request_id = int(
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

    # ========================================================
    # LOAD REQUEST BEFORE REJECTING
    # ========================================================

    pending_request = await get_schedule_request_by_id(
        request_id
    )

    if not pending_request:
        await callback.answer(
            "Schedule request not found.",
            show_alert=True,
        )
        return

    if pending_request.recipient_id != user.id:
        await callback.answer(
            "This request is not for you.",
            show_alert=True,
        )
        return

    match = pending_request.match

    was_schedule_change = (
        match.status == "scheduled"
    )

    current_scheduled_at = match.scheduled_at

    # ========================================================
    # REJECT REQUEST
    # ========================================================

    try:
        schedule_request = await reject_schedule_request(
            request_id=request_id,
            user_id=user.id,
        )

    except ValueError as error:
        await callback.answer(
            str(error),
            show_alert=True,
        )
        return

    requester = schedule_request.requested_by
    recipient = schedule_request.recipient
    proposed_at = schedule_request.proposed_at

    # ========================================================
    # REQUESTER NOTIFICATION
    # ========================================================

    if was_schedule_change:
        requester_text = schedule_change_rejected_message(
            opponent=recipient,
            current_scheduled_at=current_scheduled_at,
        )
    else:
        requester_text = schedule_request_rejected_message(
            opponent=recipient,
            proposed_at=proposed_at,
        )

    await callback.bot.send_message(
        chat_id=requester.telegram_id,
        text=requester_text,
    )

    # ========================================================
    # RECIPIENT CONFIRMATION
    # ========================================================

    if was_schedule_change:
        recipient_text = schedule_change_rejected_message(
            opponent=requester,
            current_scheduled_at=current_scheduled_at,
        )
    else:
        recipient_text = schedule_request_rejected_message(
            opponent=requester,
            proposed_at=proposed_at,
        )

    await callback.message.edit_text(
        recipient_text
    )

    await callback.answer()
