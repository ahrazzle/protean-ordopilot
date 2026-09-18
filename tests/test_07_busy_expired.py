"""7. busy-expired: busy seat parks; expired seat takeovers bump epoch;
live seat + steal is recorded."""
from tests.conftest import redacted_msg, seed, sessions_of

from orda import dispatcher, router
from orda.intake import utcnow_rfc3339
from orda.ledger import idempotency_key


class TestBusyExpired:
    def test_busy_parks(self, state):
        seed(state["catalog"], state["backend"], [
            ("busy", "busy topic ongoing work queue"),
        ])
        ref = state["catalog"].acquire_seat("busy", "someone-else")
        # Recent delivery => busy.
        state["ledger"].record({
            "idempotency_key": idempotency_key("hash0",
                                              ref["session_id"]),
            "message_id": "m0", "canonical_hash": "hash0",
            "target_session_id": ref["session_id"],
            "decision_kind": "CONTINUE", "provider": "p", "model": "m",
            "result": "delivered", "ts_utc": utcnow_rfc3339()})
        msg = redacted_msg("/busy please help with the queue")
        decision = router.route(msg, sessions_of(state["catalog"]))
        assert decision["kind"] == "CONTINUE"
        result = dispatcher.dispatch(msg, decision, state["catalog"],
                                     state["ledger"], state["backend"])
        assert result["result"] == "parked-busy"
        assert "busy(" in result["reason"]

    def test_expired_takeover_bumps_epoch(self, state):
        seed(state["catalog"], state["backend"], [("ops", "ops oncall")])
        state["catalog"].acquire_seat("ops", "gone-writer", ttl_s=-1)
        ref = state["catalog"].takeover_expired("ops", "me")
        assert ref["seat_holder"] == "me"
        assert ref["seat_epoch"] == 1
        kinds = [e["type"] for e in state["catalog"].events()]
        assert "seat-takeover" in kinds

    def test_live_steal_recorded(self, state):
        seed(state["catalog"], state["backend"], [("ops", "ops oncall")])
        state["catalog"].acquire_seat("ops", "other")
        ref = state["catalog"].steal_seat("ops", "me")
        assert ref["seat_holder"] == "me"
        assert ref["seat_epoch"] == 1
        takeovers = [e for e in state["catalog"].events()
                     if e["type"] == "seat-takeover"]
        assert takeovers and takeovers[0]["explicit_steal"] is True
