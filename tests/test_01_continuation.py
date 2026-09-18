"""1. continuation: known-topic message -> CONTINUE, right session, >= floor."""
from tests.conftest import redacted_msg, seed, sessions_of

from courier import ROUTER_CONFIDENCE_FLOOR, dispatcher, router


class TestContinuation:
    def test_continue_right_session(self, state):
        seed(state["catalog"], state["backend"], [
            ("refund-policy", "refund policy returns warranty claims process"),
            ("billing", "billing invoices payments charges statements"),
        ])
        msg = redacted_msg(
            "What is our refund policy for damaged items?")
        decision = router.route(msg, sessions_of(state["catalog"]))
        assert decision["kind"] == "CONTINUE"
        assert decision["target_slug"] == "refund-policy"
        assert decision["confidence"] >= ROUTER_CONFIDENCE_FLOOR
        assert decision["provider"] and decision["model"]

        result = dispatcher.dispatch(msg, decision, state["catalog"],
                                     state["ledger"], state["backend"])
        assert result["result"] == "delivered"
        assert result["target_session_id"] == decision["target_session_id"]

    def test_explicit_slug_continues(self, state):
        seed(state["catalog"], state["backend"], [
            ("refund-policy", "refund policy returns warranty claims"),
        ])
        msg = redacted_msg("/refund-policy any update on my case?")
        decision = router.route(msg, sessions_of(state["catalog"]))
        assert decision["kind"] == "CONTINUE"
        assert decision["confidence"] == 1.0
