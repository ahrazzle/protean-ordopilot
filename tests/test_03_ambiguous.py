"""3. ambiguous: two close topics (margin < 0.10) -> ambiguous bucket."""
from tests.conftest import redacted_msg, seed, sessions_of

from courier import router


class TestAmbiguous:
    def test_close_topics_escalate_no_autocreate(self, state):
        seed(state["catalog"], state["backend"], [
            ("billing-help", "billing invoices payments refunds statements"),
            ("billing-support", "billing invoices payments refunds receipts"),
        ])
        before = len(state["catalog"].list_sessions())
        msg = redacted_msg("billing invoices payments question")
        decision = router.route(msg, sessions_of(state["catalog"]))
        assert decision["kind"] == "ESCALATE"
        assert "ambigu" in decision["reason"]
        # Nothing auto-created, nothing delivered.
        assert len(state["catalog"].list_sessions()) == before
        assert state["ledger"].count() == 0
