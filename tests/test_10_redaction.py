"""10. secret-redaction: fixtures redacted before router call; telemetry
carries no payload substring."""
import pytest

from courier import intake, redact, router
from courier.redact import RedactionBlocked, telemetry_record
from courier.router import StubRouterModel

SECRETS = {
    "api_key": "sk-abcdefghijklmnop123456",
    "aws_key": "AKIAIOSFODNN7EXAMPLE",
    "private": "-----BEGIN RSA PRIVATE KEY-----",
    "gh_token": "ghp_abcdefghijklmnop123456",
    "bearer": "Bearer abcdef123456._-~+/=",
}


class TestSecretRedaction:
    def test_fixtures_redacted(self):
        for name, secret in SECRETS.items():
            msg = intake.make_message("deploy with %s now" % secret)
            red, report = redact.redact_message(msg)
            assert secret not in red["text"], name
            assert report["count"] >= 1, name
            assert red["_redacted"] is True

    def test_router_sees_only_redacted(self):
        secret = SECRETS["api_key"]
        msg = intake.make_message("deploy with %s now" % secret)
        red, _ = redact.redact_message(msg)
        spy = StubRouterModel([{"kind": "NEW", "target_slug": None,
                                "confidence": 0.8, "reason": "spy",
                                "required_context": []}])
        router.route(red, [], classifier=spy)
        seen = spy.calls[0]["text"]
        assert secret not in seen
        assert "[REDACTED" in seen

    def test_unredacted_refused(self):
        msg = intake.make_message("plain hello")
        with pytest.raises(ValueError):
            router.route(msg, [])

    def test_telemetry_has_no_payload(self):
        secret = SECRETS["gh_token"]
        msg = intake.make_message("use %s here" % secret)
        red, report = redact.redact_message(msg)
        rec = telemetry_record(red, decision={"kind": "NEW",
                                              "target_session_id": "s1",
                                              "confidence": 0.8,
                                              "provider": "p", "model": "m"},
                               report=report)
        blob = str(rec)
        assert secret not in blob
        assert "use %s here" % secret not in blob
        assert rec["redaction_count"] >= 1

    def test_strict_blocks(self):
        msg = intake.make_message("key %s" % SECRETS["api_key"])
        with pytest.raises(RedactionBlocked):
            redact.redact_message(msg, {"strict": True})

    def test_emails_pass_by_default(self):
        msg = intake.make_message("contact ops@example.com today")
        red, report = redact.redact_message(msg)
        assert "ops@example.com" in red["text"]
        assert report["count"] == 0
        red2, report2 = redact.redact_message(msg, {"redact_emails": True})
        assert "ops@example.com" not in red2["text"]
        assert report2["count"] == 1
