import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.matches import (
    accept_schedule_request,
    MATCH_STATUS_AWAITING_SCHEDULE,
    MATCH_STATUS_SCHEDULED,
    SCHEDULE_REQUEST_ACCEPTED,
)


class ScheduleAcceptanceUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_accept_loads_relationships_and_returns_request(self):
        proposed_at = datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc)
        match = SimpleNamespace(
            id=123,
            status=MATCH_STATUS_AWAITING_SCHEDULE,
            scheduled_at=None,
        )
        requester = SimpleNamespace(id=1)
        recipient = SimpleNamespace(id=2)
        request = SimpleNamespace(
            id=456,
            match_id=123,
            recipient_id=2,
            proposed_at=proposed_at,
            status="pending",
            match=match,
            requested_by=requester,
            recipient=recipient,
        )

        session = AsyncMock()
        session.__aenter__.return_value = session
        session.__aexit__.return_value = False

        match_result = SimpleNamespace(scalar_one_or_none=lambda: match)
        request_result = SimpleNamespace(
            scalar_one_or_none=lambda: request
        )
        session.execute = AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one_or_none=lambda: 123),
                match_result,
                request_result,
            ]
        )

        with patch(
            "services.matches.AsyncSessionLocal",
            return_value=session,
        ):
            result = await accept_schedule_request(456, 2)

        self.assertIs(result, request)
        self.assertIs(result.match, match)
        self.assertIs(result.requested_by, requester)
        self.assertIs(result.recipient, recipient)
        self.assertEqual(result.status, SCHEDULE_REQUEST_ACCEPTED)
        self.assertEqual(match.status, MATCH_STATUS_SCHEDULED)
        self.assertEqual(match.scheduled_at, proposed_at)
        session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
