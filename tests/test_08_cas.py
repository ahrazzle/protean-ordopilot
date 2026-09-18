"""8. cas-conflict: stale expected_rev -> conflict, retry once, escalate."""
import pytest

from tests.conftest import seed

from orda.catalog import ConflictError


class TestCasConflict:
    def test_stale_rev_conflicts_no_overwrite(self, state):
        seed(state["catalog"], state["backend"], [("ops", "ops oncall")])
        state["catalog"].acquire_seat("ops", "me")
        ref = state["catalog"].get("ops")
        rev = ref["revision"]
        # Concurrent writer moves first.
        state["catalog"].update_session("ops", rev, summary="writer-b",
                                        holder="me")
        with pytest.raises(ConflictError):
            state["catalog"].update_session("ops", rev, summary="writer-a",
                                            holder="me")
        # No silent overwrite: writer-b's summary stands.
        assert state["catalog"].get("ops")["summary"] == "writer-b"
        # Caller re-reads and retries once -> succeeds.
        fresh = state["catalog"].get("ops")
        ok = state["catalog"].update_session("ops", fresh["revision"],
                                             summary="writer-a-retry",
                                             holder="me")
        assert ok["summary"] == "writer-a-retry"
        # A further stale write still conflicts (then the caller escalates).
        with pytest.raises(ConflictError):
            state["catalog"].update_session("ops", rev, summary="late",
                                            holder="me")
