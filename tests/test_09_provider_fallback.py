"""9. provider-fallback-timeout: tier timeout -> next tier with fallback_from;
total outage -> ESCALATE."""
import pytest

from orda import policy
from orda.policy import ModelConfig, PolicyExhausted


def _cfg():
    return ModelConfig(
        cheap={"provider": "cheap", "model": "cheap-v1"},
        main={"provider": "main", "model": "main-v0"})


class TestProviderFallback:
    def test_timeout_falls_over_with_record(self):
        def call(provider, model):
            if provider == "cheap":
                raise TimeoutError("router tier 8s timeout")
            return {"answer": "ok"}

        result, provider, model, fallback = policy.call_with_fallback(
            _cfg(), call, role="router")
        assert result == {"answer": "ok"}
        assert (provider, model) == ("main", "main-v0")
        assert fallback is not None and "timeout" in fallback["error"]

    def test_total_outage_escalates(self):
        def call(provider, model):
            raise TimeoutError("down: %s" % provider)

        with pytest.raises(PolicyExhausted):
            policy.call_with_fallback(_cfg(), call, role="router")
        decision = policy.escalate_unavailable("router")
        assert decision["kind"] == "ESCALATE"
        assert "provider-unavailable" in decision["reason"]

    def test_free_tier_gated_off(self):
        cfg = ModelConfig(
            free={"provider": "portal", "model": "blockrun/free"},
            main={"provider": "main", "model": "main-v0"})
        # Configured but neither allowed nor verified -> skipped.
        assert policy.free_tier_enabled(cfg) is False
        assert all(p != "portal"
                   for _, p, _ in policy.resolve_chain(cfg, "router"))
        cfg.free_tier_allowed = True
        cfg.free_verified = True
        assert policy.free_tier_enabled(cfg) is True
        assert any(p == "portal"
                   for _, p, _ in policy.resolve_chain(cfg, "router"))
