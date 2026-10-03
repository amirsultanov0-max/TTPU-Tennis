from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from database.database import AsyncSessionLocal
from database.models import Match, ScheduleRequest, User


# ============================================================
# MATCH CONSTANTS
# ============================================================


ACTIVE_MATCH_STATUSES = (
    "awaiting_schedule",
    "scheduled",
)

MATCH_STATUS_AWAITING_SCHEDULE = "awaiting_schedule"
MATCH_STATUS_SCHEDULED = "scheduled"
MATCH_STATUS_COMPLETED = "completed"
MATCH_STATUS_CANCELLED = "cancelled"


# ============================================================
# RESULT CONSTANTS
# ============================================================


RESULT_STATUS_NOT_SUBMITTED = "not_submitted"
RESULT_STATUS_PENDING_CONFIRMATION = "pending_confirmation"
RESULT_STATUS_CONFIRMED = "confirmed"


# ============================================================
# SCHEDULE REQUEST CONSTANTS
# ============================================================


SCHEDULE_REQUEST_PENDING = "pending"
SCHEDULE_REQUEST_ACCEPTED = "accepted"
SCHEDULE_REQUEST_REJECTED = "rejected"


# ============================================================
# MATCH CREATION
# ============================================================


async def create_match_from_challenge(
    challenger_id: int,
    opponent_id: int,
) -> Match:
    """
    Create a match after a challenge has been accepted.

    The new match starts in the awaiting_schedule state.

    Raises:
        ValueError:
            If the players are invalid or an active match
            already exists between them.
    """

    if challenger_id == opponent_id:
        raise ValueError(
            "A player cannot play against themselves."
        )

    async with AsyncSessionLocal() as session:

        challenger = await session.get(
            User,
            challenger_id,
        )

        if not challenger:
            raise ValueError(
                "Challenger not found."
            )

        opponent = await session.get(
            User,
            opponent_id,
        )

        if not opponent:
            raise ValueError(
                "Opponent not found."
            )

        result = await session.execute(
            select(Match).where(
                Match.status.in_(ACTIVE_MATCH_STATUSES),
                or_(
                    (
                        (Match.player_one_id == challenger_id)
                        & (Match.player_two_id == opponent_id)
                    ),
                    (
                        (Match.player_one_id == opponent_id)
                        & (Match.player_two_id == challenger_id)
                    ),
                ),
            )
        )

        existing_match = result.scalar_one_or_none()

        if existing_match:
            raise ValueError(
                "There is already an active match "
                "between these players."
            )

        match = Match(
            player_one_id=challenger_id,
            player_two_id=opponent_id,
            status=MATCH_STATUS_AWAITING_SCHEDULE,
            result_status=RESULT_STATUS_NOT_SUBMITTED,
        )

        session.add(match)

        await session.commit()
        await session.refresh(match)

        return match


# ============================================================
# MATCH RETRIEVAL
# ============================================================


async def get_match_by_id(
    match_id: int,
) -> Match | None:
    """
    Get a match by ID with both players loaded.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
                selectinload(Match.result_submitted_by),
            )
            .where(
                Match.id == match_id
            )
        )

        return result.scalar_one_or_none()


async def get_matches_for_user(
    user_id: int,
) -> list[Match]:
    """
    Get all matches involving a specific user.

    Both players and the result submitter are eagerly loaded.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
                selectinload(Match.result_submitted_by),
            )
            .where(
                or_(
                    Match.player_one_id == user_id,
                    Match.player_two_id == user_id,
                )
            )
            .order_by(
                Match.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )


async def get_matches_for_telegram_user(
    telegram_id: int,
) -> tuple[User | None, list[Match]]:
    """
    Get a Telegram user and all of their matches using
    a single database session.
    """

    async with AsyncSessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if not user:
            return None, []

        matches_result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
                selectinload(Match.result_submitted_by),
            )
            .where(
                or_(
                    Match.player_one_id == user.id,
                    Match.player_two_id == user.id,
                )
            )
            .order_by(
                Match.created_at.desc()
            )
        )

        matches = list(
            matches_result.scalars().all()
        )

        return user, matches


# ============================================================
# RESULT REMINDERS
# ============================================================


async def get_matches_needing_result_reminder() -> list[Match]:
    """
    Get scheduled matches that finished at least two hours ago
    and have not received a result reminder yet.

    Only matches without a submitted result are returned.
    """

    reminder_cutoff = (
        datetime.now(timezone.utc)
        - timedelta(hours=2)
    )

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
            )
            .where(
                Match.status == MATCH_STATUS_SCHEDULED,
                Match.scheduled_at.is_not(None),
                Match.scheduled_at <= reminder_cutoff,
                Match.result_reminder_sent_at.is_(None),
                Match.result_status == RESULT_STATUS_NOT_SUBMITTED,
            )
            .order_by(
                Match.scheduled_at.asc()
            )
        )

        return list(
            result.scalars().all()
        )


async def mark_result_reminder_sent(
    match_id: int,
) -> None:
    """
    Mark a match as having received its result reminder.

    The timestamp is stored in UTC.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match).where(
                Match.id == match_id
            )
        )

        match = result.scalar_one_or_none()

        if not match:
            raise ValueError(
                "Match not found."
            )

        match.result_reminder_sent_at = (
            datetime.now(timezone.utc)
        )

        await session.commit()


# ============================================================
# RESULT SUBMISSION
# ============================================================


async def submit_match_result(
    match_id: int,
    submitted_by_id: int,
    set_1_player_one_score: int,
    set_1_player_two_score: int,
    set_2_player_one_score: int,
    set_2_player_two_score: int,
    set_3_player_one_score: int | None = None,
    set_3_player_two_score: int | None = None,
) -> Match:
    """
    Submit a Best-of-3 result for a scheduled match.

    The result is NOT considered final at this stage.

    The submitting player records the complete set scores, and
    the result enters the pending_confirmation state.

    Winner/loser, wins/losses, ranking points, and completed
    status are NOT updated until the opponent confirms.

    Raises:
        ValueError:
            If the match is invalid, the player is not involved,
            a result already exists, the match has not happened,
            or the set scores are invalid.
    """

    from services.tennis_scoring import get_match_winner

    try:
        match_winner = get_match_winner(
            set_1_player_one_score=set_1_player_one_score,
            set_1_player_two_score=set_1_player_two_score,
            set_2_player_one_score=set_2_player_one_score,
            set_2_player_two_score=set_2_player_two_score,
            set_3_player_one_score=set_3_player_one_score,
            set_3_player_two_score=set_3_player_two_score,
        )
    except ValueError as error:
        raise ValueError(str(error)) from error

    if match_winner is None:
        raise ValueError(
            "The match result is incomplete. "
            "A third set is required."
        )

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match).where(
                Match.id == match_id
            )
        )

        match = result.scalar_one_or_none()

        if not match:
            raise ValueError(
                "Match not found."
            )

        if submitted_by_id not in (
            match.player_one_id,
            match.player_two_id,
        ):
            raise ValueError(
                "You are not a player in this match."
            )

        if match.status != MATCH_STATUS_SCHEDULED:
            raise ValueError(
                "Only scheduled matches can receive a result."
            )

        if match.result_status != RESULT_STATUS_NOT_SUBMITTED:
            raise ValueError(
                "A result has already been submitted for this match."
            )

        if not match.scheduled_at:
            raise ValueError(
                "This match does not have a scheduled time."
            )

        now = datetime.now(timezone.utc)

        scheduled_at = match.scheduled_at

        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(
                tzinfo=timezone.utc
            )

        if now < scheduled_at:
            raise ValueError(
                "The scheduled match time has not passed yet."
            )

        match.set_1_player_one_score = (
            set_1_player_one_score
        )
        match.set_1_player_two_score = (
            set_1_player_two_score
        )

        match.set_2_player_one_score = (
            set_2_player_one_score
        )
        match.set_2_player_two_score = (
            set_2_player_two_score
        )

        match.set_3_player_one_score = (
            set_3_player_one_score
        )
        match.set_3_player_two_score = (
            set_3_player_two_score
        )

        match.result_submitted_by_id = submitted_by_id

        match.result_submitted_at = now

        match.result_status = (
            RESULT_STATUS_PENDING_CONFIRMATION
        )

        await session.commit()
        await session.refresh(match)

        return match

# ============================================================
# RESULT CONFIRMATION
# ============================================================

async def confirm_match_result(
    match_id: int,
    confirmed_by_id: int,
) -> Match:
    """
    Confirm a previously submitted Best-of-3 match result.

    The confirming player must be the opponent who did not
    submit the result.

    Only after confirmation do we:

        - validate the complete set scores
        - determine winner
        - determine loser
        - increment wins/losses
        - mark match completed
        - record played_at
        - mark result confirmed

    Ranking points are intentionally not modified here because
    the project does not yet define the ranking-point formula.
    """

    from services.tennis_scoring import get_match_winner

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
            )
            .where(
                Match.id == match_id
            )
        )

        match = result.scalar_one_or_none()

        if not match:
            raise ValueError(
                "Match not found."
            )

        if confirmed_by_id not in (
            match.player_one_id,
            match.player_two_id,
        ):
            raise ValueError(
                "You are not a player in this match."
            )

        if match.result_status != (
            RESULT_STATUS_PENDING_CONFIRMATION
        ):
            raise ValueError(
                "There is no result waiting for confirmation."
            )

        if match.result_submitted_by_id == confirmed_by_id:
            raise ValueError(
                "The player who submitted the result "
                "cannot confirm their own result."
            )

        # ----------------------------------------------------
        # Validate stored Best-of-3 result
        # ----------------------------------------------------

        if (
            match.set_1_player_one_score is None
            or match.set_1_player_two_score is None
            or match.set_2_player_one_score is None
            or match.set_2_player_two_score is None
        ):
            raise ValueError(
                "The submitted result is incomplete."
            )

        try:
            match_winner = get_match_winner(
                set_1_player_one_score=(
                    match.set_1_player_one_score
                ),
                set_1_player_two_score=(
                    match.set_1_player_two_score
                ),
                set_2_player_one_score=(
                    match.set_2_player_one_score
                ),
                set_2_player_two_score=(
                    match.set_2_player_two_score
                ),
                set_3_player_one_score=(
                    match.set_3_player_one_score
                ),
                set_3_player_two_score=(
                    match.set_3_player_two_score
                ),
            )
        except ValueError as error:
            raise ValueError(
                f"The submitted result is invalid: {error}"
            ) from error

        if match_winner is None:
            raise ValueError(
                "The submitted result is incomplete. "
                "A third set is required."
            )

        # ----------------------------------------------------
        # Determine winner and loser
        # ----------------------------------------------------

        if match_winner == 1:
            winner_id = match.player_one_id
            loser_id = match.player_two_id
        else:
            winner_id = match.player_two_id
            loser_id = match.player_one_id

        # ----------------------------------------------------
        # Load both players
        # ----------------------------------------------------

        player_one = await session.get(
            User,
            match.player_one_id,
        )

        player_two = await session.get(
            User,
            match.player_two_id,
        )

        if not player_one or not player_two:
            raise ValueError(
                "One or more players could not be found."
            )

        # ----------------------------------------------------
        # Finalize match
        # ----------------------------------------------------

        now = datetime.now(timezone.utc)

        match.winner_id = winner_id
        match.loser_id = loser_id

        match.status = MATCH_STATUS_COMPLETED

        match.result_status = RESULT_STATUS_CONFIRMED

        match.played_at = now

        match.result_confirmed_at = now

        # ----------------------------------------------------
        # Update player statistics
        # ----------------------------------------------------

        if winner_id == player_one.id:
            player_one.wins += 1
            player_two.losses += 1
        else:
            player_two.wins += 1
            player_one.losses += 1

        await session.commit()
        await session.refresh(match)

        return match

        # ----------------------------------------------------
        # Update player statistics
        # ----------------------------------------------------

        if winner_id == player_one.id:
            player_one.wins += 1
            player_two.losses += 1
        else:
            player_two.wins += 1
            player_one.losses += 1

        await session.commit()
        await session.refresh(match)

        return match


# ============================================================
# MATCH CANCELLATION
# ============================================================


async def cancel_match(
    match_id: int,
    user_id: int,
) -> Match:
    """
    Cancel a match.

    Only a player in the match can cancel it.

    A match can be cancelled while it is:
        - awaiting_schedule
        - scheduled

    A completed or already cancelled match cannot be cancelled.

    Any pending schedule request for the match is rejected
    automatically.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(Match)
            .options(
                selectinload(Match.player_one),
                selectinload(Match.player_two),
            )
            .where(
                Match.id == match_id
            )
        )

        match = result.scalar_one_or_none()

        if not match:
            raise ValueError(
                "Match not found."
            )

        if user_id not in (
            match.player_one_id,
            match.player_two_id,
        ):
            raise ValueError(
                "You are not a player in this match."
            )

        if match.status == MATCH_STATUS_COMPLETED:
            raise ValueError(
                "A completed match cannot be cancelled."
            )

        if match.status == MATCH_STATUS_CANCELLED:
            raise ValueError(
                "This match has already been cancelled."
            )

        if match.status not in (
            MATCH_STATUS_AWAITING_SCHEDULE,
            MATCH_STATUS_SCHEDULED,
        ):
            raise ValueError(
                "This match cannot be cancelled."
            )

        pending_requests_result = await session.execute(
            select(ScheduleRequest).where(
                ScheduleRequest.match_id == match_id,
                ScheduleRequest.status == SCHEDULE_REQUEST_PENDING,
            )
        )

        pending_requests = list(
            pending_requests_result.scalars().all()
        )

        for request in pending_requests:
            request.status = SCHEDULE_REQUEST_REJECTED

        match.status = MATCH_STATUS_CANCELLED

        await session.commit()
        await session.refresh(match)

        return match


# ============================================================
# SCHEDULE REQUESTS
# ============================================================


async def create_schedule_request(
    match_id: int,
    requested_by_id: int,
    proposed_at: datetime,
) -> ScheduleRequest:
    """
    Create an initial schedule request for a match.
    """

    return await _create_schedule_request(
        match_id=match_id,
        requested_by_id=requested_by_id,
        proposed_at=proposed_at,
        allowed_match_status=MATCH_STATUS_AWAITING_SCHEDULE,
    )


async def create_schedule_change_request(
    match_id: int,
    requested_by_id: int,
    proposed_at: datetime,
) -> ScheduleRequest:
    """
    Create a request to change the time of an already
    scheduled match.
    """

    return await _create_schedule_request(
        match_id=match_id,
        requested_by_id=requested_by_id,
        proposed_at=proposed_at,
        allowed_match_status=MATCH_STATUS_SCHEDULED,
    )


async def _create_schedule_request(
    match_id: int,
    requested_by_id: int,
    proposed_at: datetime,
    allowed_match_status: str,
) -> ScheduleRequest:
    """
    Internal helper for creating schedule requests.
    """

    if proposed_at.tzinfo is None:
        raise ValueError(
            "The proposed time must include a timezone."
        )

    async with AsyncSessionLocal() as session:

        match_result = await session.execute(
            select(Match).where(
                Match.id == match_id
            )
        )

        match = match_result.scalar_one_or_none()

        if not match:
            raise ValueError(
                "Match not found."
            )

        if match.status != allowed_match_status:

            if (
                allowed_match_status
                == MATCH_STATUS_AWAITING_SCHEDULE
            ):
                raise ValueError(
                    "This match is not waiting for a schedule."
                )

            raise ValueError(
                "This match is not currently scheduled."
            )

        if requested_by_id not in (
            match.player_one_id,
            match.player_two_id,
        ):
            raise ValueError(
                "You are not a player in this match."
            )

        if requested_by_id == match.player_one_id:
            recipient_id = match.player_two_id
        else:
            recipient_id = match.player_one_id

        pending_request_result = await session.execute(
            select(ScheduleRequest).where(
                ScheduleRequest.match_id == match_id,
                ScheduleRequest.status == SCHEDULE_REQUEST_PENDING,
            )
        )

        existing_request = (
            pending_request_result.scalar_one_or_none()
        )

        if existing_request:
            raise ValueError(
                "There is already a pending schedule request "
                "for this match."
            )

        schedule_request = ScheduleRequest(
            match_id=match_id,
            requested_by_id=requested_by_id,
            recipient_id=recipient_id,
            proposed_at=proposed_at,
            status=SCHEDULE_REQUEST_PENDING,
        )

        session.add(schedule_request)

        await session.commit()
        await session.refresh(schedule_request)

        return schedule_request


async def get_schedule_request_by_id(
    request_id: int,
) -> ScheduleRequest | None:
    """
    Get a schedule request with its related match and users.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(ScheduleRequest)
            .options(
                selectinload(ScheduleRequest.match),
                selectinload(ScheduleRequest.requested_by),
                selectinload(ScheduleRequest.recipient),
            )
            .where(
                ScheduleRequest.id == request_id
            )
        )

        return result.scalar_one_or_none()


async def get_pending_schedule_requests(
    user_id: int,
) -> list[ScheduleRequest]:
    """
    Get all pending schedule requests received by a player.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(ScheduleRequest)
            .options(
                selectinload(ScheduleRequest.match),
                selectinload(ScheduleRequest.requested_by),
                selectinload(ScheduleRequest.recipient),
            )
            .where(
                ScheduleRequest.recipient_id == user_id,
                ScheduleRequest.status == SCHEDULE_REQUEST_PENDING,
            )
            .order_by(
                ScheduleRequest.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )


async def accept_schedule_request(
    request_id: int,
    user_id: int,
) -> ScheduleRequest:
    """
    Accept a pending schedule request.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(ScheduleRequest)
            .options(
                selectinload(ScheduleRequest.match),
                selectinload(ScheduleRequest.requested_by),
                selectinload(ScheduleRequest.recipient),
            )
            .where(
                ScheduleRequest.id == request_id,
                ScheduleRequest.recipient_id == user_id,
                ScheduleRequest.status == SCHEDULE_REQUEST_PENDING,
            )
        )

        schedule_request = result.scalar_one_or_none()

        if not schedule_request:
            raise ValueError(
                "Schedule request not found or no longer pending."
            )

        match = schedule_request.match

        if match.status not in (
            MATCH_STATUS_AWAITING_SCHEDULE,
            MATCH_STATUS_SCHEDULED,
        ):
            raise ValueError(
                "This match is no longer available for scheduling."
            )

        match.scheduled_at = schedule_request.proposed_at
        match.status = MATCH_STATUS_SCHEDULED

        schedule_request.status = SCHEDULE_REQUEST_ACCEPTED

        await session.commit()
        await session.refresh(schedule_request)

        return schedule_request


async def reject_schedule_request(
    request_id: int,
    user_id: int,
) -> ScheduleRequest:
    """
    Reject a pending schedule request.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(ScheduleRequest)
            .options(
                selectinload(ScheduleRequest.match),
                selectinload(ScheduleRequest.requested_by),
                selectinload(ScheduleRequest.recipient),
            )
            .where(
                ScheduleRequest.id == request_id,
                ScheduleRequest.recipient_id == user_id,
                ScheduleRequest.status == SCHEDULE_REQUEST_PENDING,
            )
        )

        schedule_request = result.scalar_one_or_none()

        if not schedule_request:
            raise ValueError(
                "Schedule request not found or no longer pending."
            )

        match = schedule_request.match

        if match.status not in (
            MATCH_STATUS_AWAITING_SCHEDULE,
            MATCH_STATUS_SCHEDULED,
        ):
            raise ValueError(
                "This match is no longer available for scheduling."
            )

        schedule_request.status = SCHEDULE_REQUEST_REJECTED

        await session.commit()
        await session.refresh(schedule_request)

        return schedule_request