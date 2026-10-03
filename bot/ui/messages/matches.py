def my_matches_message(
    upcoming_count: int,
    needs_action_count: int,
    completed_count: int,
    cancelled_count: int,
) -> str:
    return (
        "📋 The match sheet.\n\n"
        f"Completed       {completed_count}\n"
        f"Upcoming         {upcoming_count}\n"
        f"Needs Action     {needs_action_count}\n"
        f"Cancelled        {cancelled_count}"
    )


def upcoming_empty_message() -> str:
    return "No upcoming matches yet."


def needs_action_empty_message() -> str:
    return "You're all caught up — nothing needs your attention right now."


def completed_empty_message() -> str:
    return "No completed matches yet."


def cancelled_empty_message() -> str:
    return "No cancelled matches yet."


def format_match_status(status: str) -> str:
    status_names = {
        "awaiting_schedule": "Awaiting schedule",
        "scheduled": "Scheduled",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }

    return status_names.get(
        status,
        status.replace("_", " ").title(),
    )


def match_section_title(section: str) -> str:
    titles = {
        "upcoming": "Upcoming",
        "needs_action": "Needs Action",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }

    return titles.get(
        section,
        "My Matches",
    )


def match_list_message(section: str) -> str:
    return (
        f"{match_section_title(section)}\n\n"
        "Select a match."
    )



def format_upcoming_match_summary(
    match,
    user_id: int,
) -> str:
    """Format a clean upcoming-match summary."""

    if match.player_one_id == user_id:
        current_user = match.player_one
        opponent = match.player_two
    else:
        current_user = match.player_two
        opponent = match.player_one

    competition_type = (
        match.competition_type.replace("_", " ").title()
    )

    summary = (
        f"#{match.id}  "
        f"{current_user.first_name} {current_user.last_name} "
        f"vs "
        f"{opponent.first_name} {opponent.last_name}"
        "\n\n"
        f"{competition_type}"
    )

    if match.scheduled_at:
        summary += (
            "\n"
            f"{match.scheduled_at.strftime('%B %-d, %Y at %H:%M')}"
        )
    else:
        summary += "\nTime not scheduled"

    return summary


def format_match_summary(
    match,
    user_id: int,
) -> str:
    """Format a clean completed-match summary."""

    if match.player_one_id == user_id:
        current_user = match.player_one
        opponent = match.player_two
    else:
        current_user = match.player_two
        opponent = match.player_one

    competition_type = (
        match.competition_type.replace("_", " ").title()
    )

    summary = (
        f"#{match.id}  "
        f"{current_user.first_name} {current_user.last_name} "
        f"vs "
        f"{opponent.first_name} {opponent.last_name}"
        "\n\n"
        f"{competition_type}"
    )

    if match.played_at:
        summary += (
            "\n"
            f"{match.played_at.strftime('%B %-d, %Y at %H:%M')}"
        )

    scores = []
    current_user_sets = 0
    opponent_sets = 0

    set_scores = [
        (
            match.set_1_player_one_score,
            match.set_1_player_two_score,
        ),
        (
            match.set_2_player_one_score,
            match.set_2_player_two_score,
        ),
        (
            match.set_3_player_one_score,
            match.set_3_player_two_score,
        ),
    ]

    for player_one_score, player_two_score in set_scores:
        if player_one_score is None or player_two_score is None:
            continue

        if match.player_one_id == user_id:
            current_score = player_one_score
            opponent_score = player_two_score
        else:
            current_score = player_two_score
            opponent_score = player_one_score

        scores.append(
            f"{current_score}–{opponent_score}"
        )

        if current_score > opponent_score:
            current_user_sets += 1
        elif opponent_score > current_score:
            opponent_sets += 1

    if scores:
        result = None

        if current_user_sets > opponent_sets:
            result = "Won"
        elif opponent_sets > current_user_sets:
            result = "Lost"

        score_text = "  ".join(scores)

        if result:
            summary += (
                "\n"
                f"{score_text}  ·  {result}"
            )
        else:
            summary += (
                "\n"
                f"{score_text}"
            )

    return summary


def match_empty_message(section: str) -> str:
    empty_messages = {
        "upcoming": upcoming_empty_message,
        "needs_action": needs_action_empty_message,
        "completed": completed_empty_message,
        "cancelled": cancelled_empty_message,
    }

    builder = empty_messages.get(section)

    if builder is None:
        return (
            f"{match_section_title(section)}\n\n"
            "No matches found."
        )

    return builder()


def format_match_message(
    match,
    user_id: int,
) -> str:
    if match.player_one_id == user_id:
        current_user = match.player_one
        opponent = match.player_two
    else:
        current_user = match.player_two
        opponent = match.player_one

    current_user_name = (
        f"{current_user.first_name} "
        f"{current_user.last_name}"
    )

    opponent_name = (
        f"{opponent.first_name} "
        f"{opponent.last_name}"
    )

    sections = [
        f"Match #{match.id}",
        "",
        "You",
        current_user_name,
        "",
        "Opponent",
        opponent_name,
    ]

    if match.scheduled_at:
        sections.extend(
            [
                "",
                (
                    f"{match.scheduled_at:%B %-d, %Y}"
                    f" · "
                    f"{match.scheduled_at:%H:%M}"
                ),
            ]
        )

        status = format_match_status(
            match.status
        )

        sections.append("")

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        scheduled_at = match.scheduled_at

        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(
                tzinfo=timezone.utc
            )

        if (
            match.status == "scheduled"
            and scheduled_at <= now
        ):
            sections.append(
                "Match time has passed."
            )
        else:
            sections.append(status)

    else:
        sections.extend(
            [
                "",
                format_match_status(match.status),
            ]
        )

    if match.result_status in (
        "pending_confirmation",
        "confirmed",
    ):
        scores_complete = (
            match.set_1_player_one_score is not None
            and match.set_1_player_two_score is not None
            and match.set_2_player_one_score is not None
            and match.set_2_player_two_score is not None
        )

        if scores_complete:
            result_title = (
                "Submitted Result"
                if match.result_status
                == "pending_confirmation"
                else "Final Result"
            )

            sections.extend(
                [
                    "",
                    result_title,
                    (
                        f"Set 1    "
                        f"{match.set_1_player_one_score}–"
                        f"{match.set_1_player_two_score}"
                    ),
                    (
                        f"Set 2    "
                        f"{match.set_2_player_one_score}–"
                        f"{match.set_2_player_two_score}"
                    ),
                ]
            )

            if (
                match.set_3_player_one_score is not None
                and match.set_3_player_two_score is not None
            ):
                sections.append(
                    (
                        f"Set 3    "
                        f"{match.set_3_player_one_score}–"
                        f"{match.set_3_player_two_score}"
                    )
                )

        if match.result_status == "pending_confirmation":
            sections.extend(
                [
                    "",
                    (
                        "Waiting for your opponent to confirm."
                        if match.result_submitted_by_id
                        == user_id
                        else
                        "Your confirmation is required."
                    ),
                ]
            )

    return "\n".join(sections)


def result_reminder_message(
    match,
) -> str:
    player_one_name = (
        f"{match.player_one.first_name} "
        f"{match.player_one.last_name}"
    )
    player_two_name = (
        f"{match.player_two.first_name} "
        f"{match.player_two.last_name}"
    )
    return (
        "⏰ Result Reminder\n\n"
        f"Match #{match.id}\n\n"
        f"{player_one_name}  ─┐\n"
        "                  🎾\n"
        f"{player_two_name}  ─┘\n\n"
        "Your match time has passed. Please submit the result when you're ready."
    )


def result_submission_message(
    match,
) -> str:
    player_one_name = (
        f"{match.player_one.first_name} "
        f"{match.player_one.last_name}"
    )

    player_two_name = (
        f"{match.player_two.first_name} "
        f"{match.player_two.last_name}"
    )

    return (
        "🎾 Submit Result\n\n"
        f"Match #{match.id}\n\n"
        f"{player_one_name}\n"
        "vs\n"
        f"{player_two_name}\n\n"
        "Set 1\n\n"
        "Enter the score.\n"
        "Example: 6:4"
    )


def set_2_submission_message(
    player_one_score: int,
    player_two_score: int,
) -> str:
    return (
        "🎾 Submit Result\n\n"
        f"Set 1    {player_one_score}–{player_two_score} ✓\n\n"
        "Set 2\n\n"
        "Enter the score.\n"
        "Example: 3:6"
    )


def set_3_submission_message(
    set_1_player_one_score: int,
    set_1_player_two_score: int,
    set_2_player_one_score: int,
    set_2_player_two_score: int,
) -> str:
    return (
        "🎾 Submit Result\n\n"
        f"Set 1    {set_1_player_one_score}–{set_1_player_two_score} ✓\n"
        f"Set 2    {set_2_player_one_score}–{set_2_player_two_score} ✓\n\n"
        "Match tied · 1–1\n\n"
        "Set 3\n\n"
        "Enter the score.\n"
        "Example: 6:2"
    )


def submitted_result_message(
    match_id: int,
    set_1_player_one_score: int,
    set_1_player_two_score: int,
    set_2_player_one_score: int,
    set_2_player_two_score: int,
    set_3_player_one_score: int | None = None,
    set_3_player_two_score: int | None = None,
) -> str:
    lines = [
        "✓ Result Submitted",
        "",
        f"Match #{match_id}",
        "",
        (
            f"Set 1    "
            f"{set_1_player_one_score}–"
            f"{set_1_player_two_score}"
        ),
        (
            f"Set 2    "
            f"{set_2_player_one_score}–"
            f"{set_2_player_two_score}"
        ),
    ]

    if (
        set_3_player_one_score is not None
        and set_3_player_two_score is not None
    ):
        lines.append(
            (
                f"Set 3    "
                f"{set_3_player_one_score}–"
                f"{set_3_player_two_score}"
            )
        )

    lines.extend(
        [
            "",
            "Waiting for your opponent to confirm.",
        ]
    )

    return "\n".join(lines)


def confirmed_result_message(
    match,
    winner,
    loser,
) -> str:
    lines = [
        "Final Result",
        "",
        f"Match #{match.id}",
        "",
        (
            f"Set 1    "
            f"{match.set_1_player_one_score}–"
            f"{match.set_1_player_two_score}"
        ),
        (
            f"Set 2    "
            f"{match.set_2_player_one_score}–"
            f"{match.set_2_player_two_score}"
        ),
    ]

    if (
        match.set_3_player_one_score is not None
        and match.set_3_player_two_score is not None
    ):
        lines.append(
            (
                f"Set 3    "
                f"{match.set_3_player_one_score}–"
                f"{match.set_3_player_two_score}"
            )
        )

    lines.extend(
        [
            "",
            "Winner",
            f"{winner.first_name} {winner.last_name}",
            "",
            "Loser",
            f"{loser.first_name} {loser.last_name}",
            "",
            "Match completed.",
        ]
    )

    return "\n".join(lines)


def cancel_match_confirmation_message(
    opponent,
) -> str:
    return (
        "Cancel Match?\n\n"
        "Are you sure you want to cancel this match?\n\n"
        f"Your opponent, {opponent.first_name} "
        f"{opponent.last_name}, will be notified."
    )


def match_cancelled_message(
    opponent,
) -> str:
    return (
        "Match Cancelled\n\n"
        f"Your match against "
        f"{opponent.first_name} "
        f"{opponent.last_name} has been cancelled."
    )


def match_cancelled_notification_message(
    user,
) -> str:
    return (
        "Match Cancelled\n\n"
        f"{user.first_name} "
        f"{user.last_name} cancelled your match.\n\n"
        "The match has been removed from your "
        "active schedule."
    )


def score_format_error_message() -> str:
    return (
        "Invalid score format.\n\n"
        "Please enter the score as 6:4."
    )


def result_session_expired_message() -> str:
    return (
        "Your result session has expired.\n\n"
        "Please start again from My Matches."
    )


def invalid_match_result_message(error: str) -> str:
    return (
        "Invalid match result.\n\n"
        f"{error}\n\n"
        "Please enter Set 2 again.\n"
        "Example: 3:6"
    )


def score_parse_error_message(error: str) -> str:
    return (
        f"{error}\n\n"
        "Example: 6:4"
    )


def invalid_set_score_message(error: str) -> str:
    return (
        "Invalid tennis set score.\n\n"
        f"{error}\n\n"
        "Example: 6:4"
    )
