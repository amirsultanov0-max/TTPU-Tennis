from typing import Literal


Player = Literal[1, 2]


def validate_set_score(
    player_one_score: int,
    player_two_score: int,
) -> Player:
    """
    Validate a completed tennis set score.

    Supported format:
    - Normal set: 6-x with at least a 2-game advantage.
    - 7-5 is valid.
    - 7-6 is valid for a tiebreak set.

    Returns:
        1 if Player 1 won the set.
        2 if Player 2 won the set.

    Raises:
        ValueError: If the score is not a valid completed set.
    """

    if player_one_score < 0 or player_two_score < 0:
        raise ValueError("Set scores cannot be negative.")

    if player_one_score == player_two_score:
        raise ValueError(
            "A completed tennis set cannot end in a tie."
        )

    # Player 1 wins 6-x, where x <= 4.
    if player_one_score == 6 and player_two_score <= 4:
        return 1

    # Player 2 wins x-6, where x <= 4.
    if player_two_score == 6 and player_one_score <= 4:
        return 2

    # Player 1 wins 7-5.
    if player_one_score == 7 and player_two_score == 5:
        return 1

    # Player 2 wins 5-7.
    if player_two_score == 7 and player_one_score == 5:
        return 2

    # Tiebreak set: 7-6.
    if player_one_score == 7 and player_two_score == 6:
        return 1

    if player_two_score == 7 and player_one_score == 6:
        return 2

    raise ValueError(
        "Invalid tennis set score. "
        "Use scores such as 6-4, 6-0, 7-5, or 7-6."
    )


def get_set_winner(
    player_one_score: int,
    player_two_score: int,
) -> Player:
    """
    Return the winner of a valid tennis set.

    This is a small convenience wrapper around validation.
    """

    return validate_set_score(
        player_one_score=player_one_score,
        player_two_score=player_two_score,
    )


def get_match_winner(
    set_1_player_one_score: int,
    set_1_player_two_score: int,
    set_2_player_one_score: int,
    set_2_player_two_score: int,
    set_3_player_one_score: int | None = None,
    set_3_player_two_score: int | None = None,
) -> Player | None:
    """
    Determine the winner of a Best-of-3 tennis match.

    The match is completed when one player wins two sets.

    Returns:
        1 if Player 1 won the match.
        2 if Player 2 won the match.
        None if the first two sets are split 1-1
        and a third set is required.

    Raises:
        ValueError:
            If any provided set score is invalid.
            If a third set is provided when it is not needed.
            If only one of the third-set scores is provided.
    """

    set_1_winner = validate_set_score(
        player_one_score=set_1_player_one_score,
        player_two_score=set_1_player_two_score,
    )

    set_2_winner = validate_set_score(
        player_one_score=set_2_player_one_score,
        player_two_score=set_2_player_two_score,
    )

    player_one_sets = 0
    player_two_sets = 0

    if set_1_winner == 1:
        player_one_sets += 1
    else:
        player_two_sets += 1

    if set_2_winner == 1:
        player_one_sets += 1
    else:
        player_two_sets += 1

    # A player has already won 2-0.
    if player_one_sets == 2:
        if (
            set_3_player_one_score is not None
            or set_3_player_two_score is not None
        ):
            raise ValueError(
                "A third set is not needed because "
                "Player 1 already won the first two sets."
            )

        return 1

    if player_two_sets == 2:
        if (
            set_3_player_one_score is not None
            or set_3_player_two_score is not None
        ):
            raise ValueError(
                "A third set is not needed because "
                "Player 2 already won the first two sets."
            )

        return 2

    # The first two sets are split 1-1.
    # Either both third-set scores must be provided,
    # or neither may be provided.
    if (
        set_3_player_one_score is None
        and set_3_player_two_score is None
    ):
        return None

    if (
        set_3_player_one_score is None
        or set_3_player_two_score is None
    ):
        raise ValueError(
            "Both third-set scores must be provided."
        )

    set_3_winner = validate_set_score(
        player_one_score=set_3_player_one_score,
        player_two_score=set_3_player_two_score,
    )

    if set_3_winner == 1:
        player_one_sets += 1
    else:
        player_two_sets += 1

    if player_one_sets == 2:
        return 1

    return 2