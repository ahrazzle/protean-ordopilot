"""2. new-topic: novel message -> NEW with fresh session_id, min context."""
from tests.conftest import redacted_msg, seed, sessions_of

from orda import router


class TestNewTopic:
    def test_novel_message_is_new(self, state):
        seed(state["catalog"], state["backend"], [
            ("refund-policy", "refund policy returns warranty claims process"),
            ("billing", "billing invoices payments charges statements"),
        ])
        msg = redacted_msg("quantum knitting patterns for llamas under "
                           "moonlight, needles clicking")
        decision = router.route(msg, sessions_of(state["catalog"]))
        assert decision["kind"] == "NEW"
        assert decision["target_session_id"]
        assert decision["required_context"] == []

    def test_new_materializes_session(self, state):
        from orda import dispatcher
        seed(state["catalog"], state["backend"], [
            ("refund-policy", "refund policy returns warranty claims process"),
        ])
        msg = redacted_msg("quantum knitting patterns for llamas under "
                           "moonlight, needles clicking")
        decision = router.route(msg, sessions_of(state["catalog"]))
        assert decision["kind"] == "NEW"
        result = dispatcher.dispatch(msg, decision, state["catalog"],
                                     state["ledger"], state["backend"])
        assert result["result"] == "delivered"
        assert state["catalog"].get(result["target_session_id"]) is not None
