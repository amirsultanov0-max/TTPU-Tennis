from datetime import timezone
from zoneinfo import ZoneInfo


TASHKENT_TIMEZONE = ZoneInfo("Asia/Tashkent")


def format_player_name(user) -> str:
    return f"{user.first_name} {user.last_name}"


def format_match_datetime(dt, fmt: str = "%B %-d, %Y · %H:%M") -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TASHKENT_TIMEZONE).strftime(fmt)
