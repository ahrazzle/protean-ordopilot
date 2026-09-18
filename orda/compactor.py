"""Handoff compactor: pointer-based bundles within a bounded char budget.

Newest items first; oldest dropped until within HANDOFF_BUDGET_CHARS with
truncated:true. Pointers (event seqs / detail refs), never transcripts,
never secrets (redaction pass inherited).
"""

import uuid

from . import HANDOFF_BUDGET_CHARS
from .intake import utcnow_rfc3339
from .redact import redact_text


def build_handoff(from_session_id, items, to_session_id=None,
                  budget=HANDOFF_BUDGET_CHARS, summary_prefix=""):
    """items: [{summary, ref}] newest-first. Returns HandoffRecord dict."""
    safe = []
    for it in items or []:
        text, _ = redact_text(str(it.get("summary", "")))
        ref = str(it.get("ref", ""))
        safe.append({"summary": text, "ref": ref})
    # Greedily keep newest-first until the joined body fits the budget.
    kept = list(safe)
    truncated = False
    while kept and _body_size(summary_prefix, kept) > budget:
        kept.pop()
        truncated = True
    body = _join(summary_prefix, kept)
    pointers = [it["ref"] for it in kept if it["ref"]]
    context_ids = [it["ref"] for it in kept if it["ref"]]
    return {
        "handoff_id": "handoff-" + uuid.uuid4().hex[:8],
        "from_session_id": from_session_id,
        "to_session_id": to_session_id,
        "summary": body,
        "pointers": pointers,
        "context_ids": context_ids,
        "char_count": len(body),
        "truncated": truncated or len(kept) < len(safe),
        "ts_utc": utcnow_rfc3339(),
    }


def _join(prefix, items):
    lines = []
    if prefix:
        lines.append(prefix)
    for it in items:
        if it["ref"]:
            lines.append("- [%s] %s" % (it["ref"], it["summary"]))
        else:
            lines.append("- %s" % it["summary"])
    return "\n".join(lines)


def _body_size(prefix, items):
    return len(_join(prefix, items))
