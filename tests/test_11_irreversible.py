"""11. irreversible-boundary: send/publish/spend/delete/prod-write fixtures
-> APPROVAL_REQUIRED, default deny, no dispatch."""
from tests.conftest import redacted_msg, seed, sessions_of

from courier import approvals, dispatcher, router

FIXTURES = [
    ("send the contract to legal tonight", "send"),
    ("publish the release notes to the blog", "publish"),
    ("spend $50 on search ads", "spend"),
    ("delete the archive folder", "delete"),
    ("migrate the production database now", "production-write"),
    ("push this config to the external webhook", "external-write"),
]


class TestIrreversibleBoundary:
    def test_gate_requires_approval(self):
        for text, action in FIXTURES:
            msg = redacted_msg(text)
            gate, info = approvals.check(msg)
            assert gate == "APPROVAL_REQUIRED", text
            assert (info or {})["action_class"] == action, text

    def test_router_never_autodelivers(self, state):
        seed(state["catalog"], state["backend"], [
            ("ops", "ops oncall incidents deploys"),
        ])
        for text, _ in FIXTURES:
            msg = redacted_msg(text)
            decision = router.route(msg, sessions_of(state["catalog"]))
            result = dispatcher.dispatch(msg, decision, state["catalog"],
                                         state["ledger"], state["backend"])
            assert result["result"] == "held-for-approval", text
        assert state["backend"].appended == []
        assert state["ledger"].count() == 0

    def test_benign_passes_gate(self):
        msg = redacted_msg("what is our refund policy?")
        assert approvals.check(msg)[0] == "ALLOW"
