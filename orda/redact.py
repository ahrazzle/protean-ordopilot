"""Secret redaction. Runs BEFORE any router-model call.

Deny-by-default classes with patterns from explicit config. Telemetry and
the ledger store hashes/decisions/counts only, never payloads.
"""

import copy
import re

# (class_name, [regex, ...]) — explicit, auditable, no env sniffing.
BASE_PATTERNS = {
    "api_keys": [
        r"sk-[A-Za-z0-9]{16,}",
        r"AKIA[0-9A-Z]{16}",
    ],
    "private_keys": [
        r"-----BEGIN .*?PRIVATE KEY-----",
    ],
    "tokens": [
        r"gh[pousr]_[A-Za-z0-9]{16,}",
        r"xox[bpas]-[A-Za-z0-9\-]+",
        r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    ],
    "emails": [
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    ],
}

# Classes that always redact. Emails only when redact_emails:true.
DENY_CLASSES = ("api_keys", "private_keys", "tokens")


class RedactionBlocked(Exception):
    """Raised in strict mode when a deny-class secret is present."""


def _compile(config=None):
    config = config or {}
    compiled = {}
    for cls in DENY_CLASSES:
        compiled[cls] = [re.compile(p) for p in BASE_PATTERNS[cls]]
    if config.get("redact_emails", False):
        compiled["emails"] = [re.compile(p) for p in BASE_PATTERNS["emails"]]
    extra = config.get("extra_patterns", []) or []
    if extra:
        compiled.setdefault("extra", []).extend(re.compile(p) for p in extra)
    return compiled


def redact_text(text, config=None):
    """Return (redacted_text, report{count, classes})."""
    config = config or {}
    compiled = _compile(config)
    report = {"count": 0, "classes": {}}
    out = text
    for cls, patterns in compiled.items():
        for pat in patterns:
            def _sub(_m, _cls=cls):
                report["count"] += 1
                report["classes"][_cls] = report["classes"].get(_cls, 0) + 1
                return "[REDACTED:%s]" % _cls.upper().replace("_", "-")
            out = pat.sub(_sub, out)
    if config.get("strict", False) and any(
            c in report["classes"] for c in DENY_CLASSES):
        raise RedactionBlocked(
            "deny-class secret present: %s" % sorted(report["classes"]))
    return out, report


def redact_message(msg, config=None):
    """Return (redacted_message_copy, report). Marks _redacted=True."""
    redacted_text, report = redact_text(msg.get("text", ""), config)
    new_msg = copy.deepcopy(msg)
    new_msg["text"] = redacted_text
    new_msg["_redacted"] = True
    return new_msg, report


def telemetry_record(msg, decision=None, report=None):
    """Log-safe record: hashes/decisions/counts only, never payload text."""
    rec = {
        "canonical_hash_prefix": msg.get("canonical_hash", "")[:16],
        "message_id": msg.get("message_id"),
        "redaction_count": (report or {}).get("count", 0),
        "redaction_classes": sorted((report or {}).get("classes", {})),
    }
    if decision:
        rec.update({
            "decision_kind": decision.get("kind"),
            "target": decision.get("target_session_id"),
            "confidence": decision.get("confidence"),
            "provider": decision.get("provider"),
            "model": decision.get("model"),
        })
    return rec
