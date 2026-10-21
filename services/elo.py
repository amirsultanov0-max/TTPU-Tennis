"""Elo rating calculations and historical rating reconstruction."""

from decimal import Decimal, ROUND_HALF_UP
from math import sqrt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Match, User
from services.tennis_scoring import get_match_winner


START_RATING = 1000.0
CALIBRATION_MATCHES = 5
K_CALIBRATION = 120.0
K_NORMAL = 24.0
MIN_MULTIPLIER = 0.35


def expected_score(rating_a: float, rating_b: float) -> float:
    """Calculate player A's expected score using the Elo formula."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def k_factor(matches_played: int) -> float:
    """Return the K-factor based on a player's eligible-match count."""
    return (
        K_CALIBRATION
        if matches_played < CALIBRATION_MATCHES
        else K_NORMAL
    )


def dominance_multiplier(
    games_a: int,
    games_b: int,
) -> float:
    """Calculate the source formula's score-dominance multiplier."""
    games_total = games_a + games_b

    if games_total <= 0:
        raise ValueError("Total games must be positive.")

    proportion_a = games_a / games_total
    raw_multiplier = (
        2.0
        * abs(proportion_a - 0.5)
        * sqrt(games_total / 12.0)
    )

    return max(raw_multiplier, MIN_MULTIPLIER)


def calculate_rating_changes(
    rating_a: float,
    rating_b: float,
    matches_a: int,
    matches_b: int,
    games_a: int,
    games_b: int,
    winner: int,
) -> tuple[float, float]:
    """
    Return the rating changes for both players.

    winner must be 1 when A won or 2 when B won.
    Each player's K-factor is based on their own match count.
    """
    if winner not in (1, 2):
        raise ValueError("Winner must be 1 or 2.")

    multiplier = dominance_multiplier(games_a, games_b)
    expected_a = expected_score(rating_a, rating_b)
    actual_a = 1.0 if winner == 1 else 0.0

    difference_a = actual_a - expected_a

    delta_a = (
        k_factor(matches_a)
        * multiplier
        * difference_a
    )
    delta_b = (
        k_factor(matches_b)
        * multiplier
        * -difference_a
    )

    return delta_a, delta_b


def _match_game_totals(match: Match) -> tuple[int, int]:
    """Count games won by each player across all recorded sets."""
    scores = (
        (match.set_1_player_one_score, match.set_1_player_two_score),
        (match.set_2_player_one_score, match.set_2_player_two_score),
        (match.set_3_player_one_score, match.set_3_player_two_score),
    )

    games_a = 0
    games_b = 0

    for score_a, score_b in scores:
        if score_a is None and score_b is None:
            continue
        if score_a is None or score_b is None:
            raise ValueError("A set has an incomplete score.")

        games_a += score_a
        games_b += score_b

    if games_a + games_b <= 0:
        raise ValueError("Match has no recorded games.")

    return games_a, games_b


def _stored_rating(value: float) -> Decimal:
    """Keep fractional Elo precision in the database."""
    return Decimal(str(value)).quantize(Decimal("0.000001"))


def _ranking_points(value: float) -> int:
    """Convert Elo to the integer points used by the existing UI."""
    return int(
        Decimal(str(value)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


async def apply_confirmed_match_rating(
    session: AsyncSession,
    match: Match,
    player_a: User,
    player_b: User,
    winner: int,
) -> None:
    """
    Apply Elo changes inside the caller's existing transaction.

    The caller must have already validated the match result.
    This function deliberately does not commit.
    """
    games_a, games_b = _match_game_totals(match)

    rating_a = float(player_a.elo_rating)
    rating_b = float(player_b.elo_rating)

    delta_a, delta_b = calculate_rating_changes(
        rating_a=rating_a,
        rating_b=rating_b,
        matches_a=player_a.elo_matches_played,
        matches_b=player_b.elo_matches_played,
        games_a=games_a,
        games_b=games_b,
        winner=winner,
    )

    player_a.elo_rating = _stored_rating(rating_a + delta_a)
    player_b.elo_rating = _stored_rating(rating_b + delta_b)

    player_a.elo_matches_played += 1
    player_b.elo_matches_played += 1

    player_a.ranking_points = _ranking_points(
        float(player_a.elo_rating)
    )
    player_b.ranking_points = _ranking_points(
        float(player_b.elo_rating)
    )


async def rebuild_all_ratings(session: AsyncSession) -> int:
    """
    Recalculate all players from confirmed match history.

    Matches are replayed chronologically. Invalid scores or matches
    whose stored winner conflicts with the score are skipped.
    Returns the number of matches included in the recalculation.
    """
    users_result = await session.execute(select(User).order_by(User.id))
    users = list(users_result.scalars().all())

    ratings = {user.id: START_RATING for user in users}
    counts = {user.id: 0 for user in users}

    matches_result = await session.execute(
        select(Match)
        .where(
            Match.status == "completed",
            Match.result_status == "confirmed",
            Match.winner_id.is_not(None),
            Match.played_at.is_not(None),
        )
        .order_by(
            Match.played_at,
            Match.result_confirmed_at,
            Match.id,
        )
    )

    matches = list(matches_result.scalars().all())
    included = 0

    for match in matches:
        if (
            match.player_one_id not in ratings
            or match.player_two_id not in ratings
            or match.player_one_id == match.player_two_id
        ):
            continue

        try:
            score_winner = get_match_winner(
                set_1_player_one_score=match.set_1_player_one_score,
                set_1_player_two_score=match.set_1_player_two_score,
                set_2_player_one_score=match.set_2_player_one_score,
                set_2_player_two_score=match.set_2_player_two_score,
                set_3_player_one_score=match.set_3_player_one_score,
                set_3_player_two_score=match.set_3_player_two_score,
            )
            games_a, games_b = _match_game_totals(match)
        except (TypeError, ValueError):
            continue

        if score_winner is None or match.winner_id != (
            match.player_one_id
            if score_winner == 1
            else match.player_two_id
        ):
            continue

        player_a_id = match.player_one_id
        player_b_id = match.player_two_id

        delta_a, delta_b = calculate_rating_changes(
            rating_a=ratings[player_a_id],
            rating_b=ratings[player_b_id],
            matches_a=counts[player_a_id],
            matches_b=counts[player_b_id],
            games_a=games_a,
            games_b=games_b,
            winner=score_winner,
        )

        ratings[player_a_id] += delta_a
        ratings[player_b_id] += delta_b
        counts[player_a_id] += 1
        counts[player_b_id] += 1
        included += 1

    for user in users:
        user.elo_rating = _stored_rating(ratings[user.id])
        user.elo_matches_played = counts[user.id]
        user.ranking_points = _ranking_points(ratings[user.id])

    return included
