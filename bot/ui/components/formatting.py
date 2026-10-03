def format_player_name(user) -> str:
    return f"{user.first_name} {user.last_name}"


def format_match_datetime(dt) -> str:
    return dt.strftime("%B %-d, %Y · %H:%M")
