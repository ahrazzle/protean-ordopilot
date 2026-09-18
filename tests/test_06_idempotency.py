"""6. idempotency: same message twice -> duplicate-ack, single side effect."""
from tests.conftest import redacted_msg, seed, sessions_of

from courier import dispatcher, router


class TestIdempotency:
    def test_duplicate_ack_no_redelivery(self, state):
        seed(state["catalog"], state["backend"], [
            ("refund-policy", "refund policy returns warranty claims process"),
        ])
        msg = redacted_msg("What is our refund policy for damaged items?")
        decision = router.route(msg, sessions_of(state["catalog"]))
        first = dispatcher.dispatch(msg, decision, state["catalog"],
                                    state["ledger"], state["backend"])
        second = dispatcher.dispatch(msg, decision, state["catalog"],
                                     state["ledger"], state["backend"])
        assert first["result"] == "delivered"
        assert second["result"] == "duplicate-ack"
        assert second["original"]["result"] == "delivered"
        assert state["ledger"].count() == 1
        got = [m for _, m in state["backend"].appended
               if m == msg["message_id"]]
        assert len(got) == 1
