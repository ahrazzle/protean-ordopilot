"""Message intake: raw input -> canonical Message dict.

Pure and deterministic. Never calls a model. Never stores payloads in
telemetry (only hashes/counts leave this module).
"""

import hashlib
import unicodedata
import uuid
from datetime import datetime, timezone

from . import MAX_ROUTE_DEPTH  # noqa: F401  (re-exported for convenience)


def canonicalize_text(text):
    """Frozen canonicalization: NFC -> strip trailing ws per line ->
    collapse blank-line runs to one -> join with newline."""
    norm = unicodedata.normalize("NFC", text)
    lines = [ln.rstrip() for ln in norm.split("\n")]
    out = []
    blank_run = False
    for ln in lines:
        if ln.strip() == "":
            if not blank_run:
                out.append("")
            blank_run = True
        else:
            out.append(ln)
            blank_run = False
    return "\n".join(out)


def canonical_hash(text):
    return hashlib.sha256(canonicalize_text(text).encode("utf-8")).hexdigest()


def utcnow_rfc3339():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_message(text, channel="cli", sender="user", attachments=None,
                 route_depth=0, reply_to_message_id=None, message_id=None,
                 ts_utc=None):
    """Build a Message dict. Attachments are meta-only, sorted by name,
    and excluded from the hash."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("message text must be a non-empty string")
    canon = canonicalize_text(text)
    atts = sorted(attachments or [], key=lambda a: a.get("name", ""))
    for a in atts:
        if not all(k in a for k in ("name", "mime", "size")):
            raise ValueError("attachment needs name/mime/size: %r" % (a,))
    return {
        "message_id": message_id or str(uuid.uuid4()),
        "canonical_hash": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
        "channel": channel,
        "sender": sender,
        "ts_utc": ts_utc or utcnow_rfc3339(),
        "text": canon,
        "attachments": atts,
        "route_depth": int(route_depth),
        "reply_to_message_id": reply_to_message_id,
        "_redacted": False,
    }


def validate_message(msg):
    required = ("message_id", "canonical_hash", "channel", "sender",
                "ts_utc", "text", "route_depth")
    for k in required:
        if k not in msg:
            raise ValueError("message missing field: %s" % k)
    expect = hashlib.sha256(
        canonicalize_text(msg["text"]).encode("utf-8")).hexdigest()
    if expect != msg["canonical_hash"]:
        raise ValueError("canonical_hash mismatch (integrity)")
    return True
