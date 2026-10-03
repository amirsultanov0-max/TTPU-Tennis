def profile_message(
    user,
    rank: int,
    total_players: int,
) -> str:
    matches_played = user.wins + user.losses

    if 10 <= rank % 100 <= 20:
        ordinal = f"{rank}th"
    else:
        suffixes = {1: "st", 2: "nd", 3: "rd"}
        ordinal = f"{rank}{suffixes.get(rank % 10, 'th')}"

    win_rate = (
        f"{(user.wins / matches_played * 100):.0f}%"
        if matches_played > 0
        else "0%"
    )

    return (
        "🎾 My Tennis Profile\n\n"
        "Standing\n"
        f"{ordinal} place · {user.ranking_points} points\n\n"
        "Stats\n"
        f"{user.wins} wins | {user.losses} losses\n"
        f"{matches_played} matches played | {win_rate} win rate\n\n"
        f"{user.group.name} · Student ID {user.student_id}\n"
        f"{user.first_name} {user.last_name}"
    )
