from bot.ui.components.formatting import format_match_datetime


def schedule_match_message() -> str:
    return (
        "📅 Choose a date\n\n"
        "Please enter the date in this format:\n"
        "DD-MM-YYYY\n\n"
        "Example: 31-10-2026"
    )


def change_match_time_message() -> str:
    return (
        "📅 Choose a new date\n\n"
        "Please enter the date in this format:\n"
        "DD-MM-YYYY\n\n"
        "Example: 31-10-2026"
    )


def choose_time_message() -> str:
    return (
        "🕐 Choose a time\n\n"
        "Please enter the time in this format:\n"
        "HH:MM\n\n"
        "Example: 18:30"
    )


def invalid_date_format_message() -> str:
    return (
        "Invalid date format.\n\n"
        "Use: DD-MM-YYYY\n"
        "Example: 31-10-2026"
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
        "\U0001F4E8 Schedule request sent\n\n"
        "\U0001F3BE Match time\n\n"
        f"{format_match_datetime(scheduled_at, '%B %-d, %Y')} · {format_match_datetime(scheduled_at, '%H:%M')}\n\n"
        f"Waiting for {opponent.first_name} "
        f"{opponent.last_name} to respond."
    )


def schedule_change_sent_message(
    scheduled_at,
    opponent,
) -> str:
    return (
        "📨 Schedule Change Sent\n\n"
        f"🎾 {format_match_datetime(scheduled_at, '%B %-d, %Y')} · "
        f"{format_match_datetime(scheduled_at, '%H:%M')}\n\n"
        f"Waiting for {opponent.first_name} "
        f"{opponent.last_name}.\n\n"
        "Your current time stays unchanged until they accept."
    )


def schedule_request_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "📨 Schedule request\n\n"
        f"🎾 {requester.first_name} {requester.last_name} proposed:\n\n"
        f"{format_match_datetime(scheduled_at, '%B %-d, %Y')} · {format_match_datetime(scheduled_at, '%H:%M')}\n\n"
        "Would you like to play at this time?"
    )


def schedule_change_request_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "📨 Schedule Change\n\n"
        f"🎾 {requester.first_name} {requester.last_name} "
        "proposed:\n\n"
        f"{format_match_datetime(scheduled_at, '%B %-d, %Y')} · {format_match_datetime(scheduled_at, '%H:%M')}\n\n"
        "Your current time stays unchanged until you accept."
    )


def match_scheduled_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "🎉 Match Scheduled\n\n"
        f"📅 {format_match_datetime(scheduled_at, '%B %-d, %Y')} · "
        f"{format_match_datetime(scheduled_at, '%H:%M')}\n\n"
        "See you on court! 🎾"
    )


def schedule_accepted_confirmation_message(
    requester,
    scheduled_at,
) -> str:
    return (
        "✅ Match scheduled\n\n"
        f"You accepted {requester.first_name} "
        f"{requester.last_name}'s proposal.\n\n"
        f"{format_match_datetime(scheduled_at, '%B %-d, %Y')} · {format_match_datetime(scheduled_at, '%H:%M')}"
    )


def schedule_change_accepted_message(
    scheduled_at,
) -> str:
    return (
        "🎉 Match Scheduled\n\n"
        f"📅 {format_match_datetime(scheduled_at, '%B %-d, %Y')} · "
        f"{format_match_datetime(scheduled_at, '%H:%M')}\n\n"
        "See you on court! 🎾"
    )


def schedule_request_rejected_message(
    opponent,
    proposed_at,
) -> str:
    return (
        "↩️ Schedule request declined\n\n"
        f"{opponent.first_name} {opponent.last_name} "
        "declined your proposed time.\n\n"
        f"{format_match_datetime(proposed_at, '%B %-d, %Y')} · {format_match_datetime(proposed_at, '%H:%M')}\n\n"
        "You can propose another time."
    )


def schedule_change_rejected_message(
    opponent,
    current_scheduled_at,
) -> str:
    return (
        "↩️ Schedule request declined\n\n"
        f"{opponent.first_name} {opponent.last_name} "
        "rejected your new proposed time.\n\n"
        "Your current match time remains unchanged.\n\n"
        f"{format_match_datetime(current_scheduled_at, '%B %-d, %Y')} · "
        f"{format_match_datetime(current_scheduled_at, '%H:%M')}"
    )
