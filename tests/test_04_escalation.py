"""4. escalation: forced low-confidence/timeout -> main-model record, then
clarification question."""
from tests.conftest import redacted_msg, seed, sessions_of

from orda import router
from orda.router import RouterTimeout, StubRouterModel


class TestEscalation:
    def _sessions(self, state):
        seed(state["catalog"], state["backend"], [
            ("billing-help", "billing invoices payments refunds statements"),
            ("billing-support", "billing invoices payments refunds receipts"),
        ])
        return sessions_of(state["catalog"])

    def test_timeout_then_main_model(self, state):
        sessions = self._sessions(state)
        msg = redacted_msg("billing invoices payments question")
        clf = StubRouterModel([RouterTimeout("t1 boom"),
                               RouterTimeout("retry boom")])
        main = StubRouterModel([{"kind": "CONTINUE",
                                 "target_slug": "billing-help",
                                 "confidence": 0.9,
                                 "reason": "main model picks help",
                                 "required_context": []}])
        decision, steps = router.route_with_escalation(
            msg, sessions, classifier=clf, main_classifier=main,
            provider="cheap", model="router-small",
            main_provider="main", main_model="main-model-v0")
        kinds = [s["step"] for s in steps]
        assert kinds[:3] == ["router-t1", "router-retry", "main-model"]
        assert all("provider" in s and "model" in s for s in steps)
        assert decision["kind"] == "CONTINUE"
        assert decision["target_slug"] == "billing-help"
        assert decision["provider"] == "main"

    def test_outage_then_clarification(self, state):
        sessions = self._sessions(state)
        msg = redacted_msg("billing invoices payments question")
        clf = StubRouterModel([RouterTimeout("t1"), RouterTimeout("retry")])
        decision, steps = router.route_with_escalation(
            msg, sessions, classifier=clf, main_classifier=None)
        assert [s["step"] for s in steps] == [
            "router-t1", "router-retry", "main-model", "clarification"]
        assert decision["kind"] == "ESCALATE"
        assert "billing-help" in decision["reason"]
        assert "billing-support" in decision["reason"]

    def test_depth_overflow_terminal(self, state):
        from orda import intake, redact
        raw = intake.make_message("anything at all", route_depth=99)
        msg, _ = redact.redact_message(raw)
        decision, steps = router.route_with_escalation(msg, [])
        assert decision["kind"] == "ESCALATE"
        assert decision["reason"].startswith("route-depth-overflow")
