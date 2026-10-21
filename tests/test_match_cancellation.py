import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.matches import (
    cancel_match,
    MATCH_STATUS_CANCELLED,
    MATCH_STATUS_SCHEDULED,
    RESULT_STATUS_NOT_SUBMITTED,
    RESULT_STATUS_PENDING_CONFIRMATION,
    SCHEDULE_REQUEST_PENDING,
    SCHEDULE_REQUEST_REJECTED,
)


def make_match(
    status=MATCH_STATUS_SCHEDULED,
    result_status=RESULT_STATUS_NOT_SUBMITTED,
    result_submitted_by_id=None,
):
    return SimpleNamespace(
        id=123,
        player_one_id=1,
        player_two_id=2,
        status=status,
        result_status=result_status,
        result_submitted_by_id=result_submitted_by_id,
        not_played_requested_by_id=None,
        not_played_requested_at=None,
    )


def make_session(match, requests=None):
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False

    match_result = SimpleNamespace(
        scalar_one_or_none=lambda: match
    )
    requests_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: requests or []
        )
    )

    session.execute = AsyncMock(
        side_effect=[match_result, requests_result]
    )
    return session


class MatchCancellationTests(unittest.IsolatedAsyncioTestCase):

    async def test_normal_cancellation_succeeds(self):
        match = make_match()
        session = make_session(match)

        with patch(
            "services.matches.AsyncSessionLocal",
            return_value=session,
        ):
            result = await cancel_match(123, 1)

        self.assertIs(result, match)
        self.assertEqual(match.status, MATCH_STATUS_CANCELLED)
        session.commit.assert_awaited_once()

    async def test_non_player_cannot_cancel_match(self):
        match = make_match()
        session = make_session(match)

        with patch(
            "services.matches.AsyncSessionLocal",
            return_value=session,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "not a player in this match",
            ):
                await cancel_match(123, 999)

        self.assertEqual(match.status, MATCH_STATUS_SCHEDULED)
        session.commit.assert_not_awaited()

    async def test_pending_result_prevents_cancellation(self):
        match = make_match(
            result_status=RESULT_STATUS_PENDING_CONFIRMATION,
            result_submitted_by_id=1,
        )
        session = make_session(match)

        with patch(
            "services.matches.AsyncSessionLocal",
            return_value=session,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "submitted result cannot be cancelled",
            ):
                await cancel_match(123, 1)

        self.assertEqual(match.status, MATCH_STATUS_SCHEDULED)
        session.commit.assert_not_awaited()

    async def test_already_cancelled_match_is_rejected(self):
        match = make_match(status=MATCH_STATUS_CANCELLED)
        session = make_session(match)

        with patch(
            "services.matches.AsyncSessionLocal",
            return_value=session,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "already been cancelled",
            ):
                await cancel_match(123, 1)

        session.commit.assert_not_awaited()

    async def test_cancellation_rejects_pending_schedule_requests(self):
        match = make_match()
        request = SimpleNamespace(status=SCHEDULE_REQUEST_PENDING)
        session = make_session(match, [request])

        with patch(
            "services.matches.AsyncSessionLocal",
            return_value=session,
        ):
            await cancel_match(123, 1)

        self.assertEqual(match.status, MATCH_STATUS_CANCELLED)
        self.assertEqual(request.status, SCHEDULE_REQUEST_REJECTED)
        session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
