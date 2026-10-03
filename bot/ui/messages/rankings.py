def rankings_message(
    players,
    total_players: int,
) -> str:
    if not players:
        return (
            "TTPU Tennis Rankings\n\n"
            "No players have registered yet."
        )

    lines = [
        "TTPU Tennis Rankings",
        "",
    ]

    for position, player in enumerate(players, start=1):
        lines.append(
            f"{position}. "
            f"{player.first_name} "
            f"{player.last_name} · "
            f"{player.ranking_points} pts"
        )

    lines.extend(
        [
            "",
            f"{total_players} players",
        ]
    )

    return "\n".join(lines)
