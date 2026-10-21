import unittest
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace

from services.elo import (
    CALIBRATION_MATCHES,
    K_CALIBRATION,
    K_NORMAL,
    MIN_MULTIPLIER,
    apply_confirmed_match_rating,
    calculate_rating_changes,
    dominance_multiplier,
    expected_score,
    k_factor,
)


class EloTests(unittest.TestCase):
    def test_equal_ratings_have_equal_expected_scores(self):
        self.assertAlmostEqual(expected_score(1000, 1000), 0.5)

    def test_higher_rated_player_is_expected_to_win_more_often(self):
        self.assertGreater(expected_score(1200, 1000), 0.5)
        self.assertLess(expected_score(800, 1000), 0.5)

    def test_calibration_k_factor_applies_to_first_five_matches(self):
        for count in range(CALIBRATION_MATCHES):
            self.assertEqual(k_factor(count), K_CALIBRATION)
        self.assertEqual(k_factor(CALIBRATION_MATCHES), K_NORMAL)

    def test_dominance_multiplier_has_a_minimum(self):
        self.assertEqual(dominance_multiplier(6, 6), MIN_MULTIPLIER)

    def test_dominance_multiplier_increases_with_a_decisive_score(self):
        close_score = dominance_multiplier(7, 6)
        decisive_score = dominance_multiplier(12, 3)
        self.assertGreater(decisive_score, close_score)

    def test_winner_gains_rating_against_equal_rated_opponent(self):
        delta_a, delta_b = calculate_rating_changes(
            rating_a=1000,
            rating_b=1000,
            matches_a=0,
            matches_b=0,
            games_a=10,
            games_b=8,
            winner=1,
        )
        self.assertGreater(delta_a, 0)
        self.assertLess(delta_b, 0)

    def test_upset_rewards_lower_rated_winner_more(self):
        upset_delta, _ = calculate_rating_changes(
            rating_a=800,
            rating_b=1200,
            matches_a=0,
            matches_b=0,
            games_a=10,
            games_b=8,
            winner=1,
        )
        expected_winner_delta, _ = calculate_rating_changes(
            rating_a=1200,
            rating_b=800,
            matches_a=0,
            matches_b=0,
            games_a=10,
            games_b=8,
            winner=1,
        )
        self.assertGreater(upset_delta, expected_winner_delta)


class EloApplicationTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmed_win_updates_ratings_counts_and_points(self):
        player_a = SimpleNamespace(
            elo_rating=Decimal("1000.000000"),
            elo_matches_played=0,
            ranking_points=1000,
        )
        player_b = SimpleNamespace(
            elo_rating=Decimal("1000.000000"),
            elo_matches_played=0,
            ranking_points=1000,
        )

        match = SimpleNamespace(
            set_1_player_one_score=6,
            set_1_player_two_score=4,
            set_2_player_one_score=6,
            set_2_player_two_score=3,
            set_3_player_one_score=None,
            set_3_player_two_score=None,
        )
        original_scores = (
            match.set_1_player_one_score,
            match.set_1_player_two_score,
            match.set_2_player_one_score,
            match.set_2_player_two_score,
            match.set_3_player_one_score,
            match.set_3_player_two_score,
        )

        await apply_confirmed_match_rating(
            session=None,
            match=match,
            player_a=player_a,
            player_b=player_b,
            winner=1,
        )

        self.assertGreater(player_a.elo_rating, Decimal("1000"))
        self.assertLess(player_b.elo_rating, Decimal("1000"))

        self.assertEqual(player_a.elo_matches_played, 1)
        self.assertEqual(player_b.elo_matches_played, 1)

        for player in (player_a, player_b):
            expected_points = int(
                player.elo_rating.quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )
            self.assertEqual(player.ranking_points, expected_points)

        current_scores = (
            match.set_1_player_one_score,
            match.set_1_player_two_score,
            match.set_2_player_one_score,
            match.set_2_player_two_score,
            match.set_3_player_one_score,
            match.set_3_player_two_score,
        )
        self.assertEqual(current_scores, original_scores)


if __name__ == "__main__":
    unittest.main()
