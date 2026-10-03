def schedule_match_message() -> str:
    return (
        "Schedule Match\n\n"
        "Choose a date.\n\n"
        "Format: YYYY-MM-DD\n"
        "Example: 2026-10-10"
    )


def change_match_time_message() -> str:
    return (
        "Change Match Time\n\n"
        "Choose a new date.\n\n"
        "Format: YYYY-MM-DD\n"
        "Example: 2026-10-10"
    )


def choose_time_message() -> str:
    return (
        "Choose a time.\n\n"
        "Format: HH:MM\n"
        "Example: 18:30"
    )


def invalid_date_format_message() -> str:
    return (
        "Invalid date format.\n\n"
        "Use: YYYY-MM-DD\n"
        "Example: 2026-10-10"
    )


def invalid_time_format_message() -> str:
    return (
        "Invalid time format.\n\n"
        "Use: HH:MM\n"
        "Example: 18:30"
    )


def schedule_request_sent_message(
    scheduled_at,
    opponent,
) -> str:
    return (
        "Schedule Request Sent\n\n"
        "Match time\n\n"
        f"{scheduled_at:%B %-d, %Y} · {scheduled_at:%H:%M}\n\n"
        f"Waiting for {opponent.first_name} "
        f"{opponent.last_name} to respond."
    )


def schedule_change_sent_message(
    scheduled_at,
    opponent,
) -> str:
    return (
        "Schedule Change Sent\n\n"
        "New match time\n\n"
        f"{scheduled_at:%B %-d, %Y} · {scheduled_at:%H:%M}\n\n"
        f"Waiting for {opponent.first_name} "
        f"{opponent.last_name} to respond.\n\n"
        "Your current match time will remain unchanged "
        "until they accept."
    )


def schedule_request_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "Schedule Request\n\n"
        f"{requester.first_name} {requester.last_name} proposed:\n\n"
        f"{scheduled_at:%B %-d, %Y} · {scheduled_at:%H:%M}\n\n"
        "Would you like to play at this time?"
    )


def schedule_change_request_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "Change Match Time\n\n"
        f"{requester.first_name} {requester.last_name} proposed a new time:\n\n"
        f"{scheduled_at:%B %-d, %Y} · {scheduled_at:%H:%M}\n\n"
        "Your current match time will remain unchanged\n"
        "until you accept.\n\n"
        "Would you like to accept this change?"
    )


def match_scheduled_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "Match Scheduled\n\n"
        f"{requester.first_name} {requester.last_name} "
        "accepted your proposal.\n\n"
        f"{scheduled_at:%B %-d, %Y} · {scheduled_at:%H:%M}"
    )


def schedule_change_accepted_message(
    scheduled_at,
) -> str:
    return (
        "Match Scheduled\n\n"
        "The match time has been updated.\n\n"
        f"{scheduled_at:%B %-d, %Y} · {scheduled_at:%H:%M}"
    )


def schedule_request_rejected_message(
    opponent,
    proposed_at,
) -> str:
    return (
        "Schedule Request Rejected\n\n"
        f"{opponent.first_name} {opponent.last_name} "
        "rejected your proposed time.\n\n"
        f"{proposed_at:%B %-d, %Y} · {proposed_at:%H:%M}\n\n"
        "You can propose another time."
    )


def schedule_change_rejected_message(
    opponent,
    current_scheduled_at,
) -> str:
    return (
        "Schedule Request Rejected\n\n"
        f"{opponent.first_name} {opponent.last_name} "
        "rejected your new proposed time.\n\n"
        "Your current match time remains unchanged.\n\n"
        f"{current_scheduled_at:%B %-d, %Y} · "
        f"{current_scheduled_at:%H:%M}"
    )
