"""Approval gate: irreversible actions NEVER auto-route.

Default deny; approval is an explicit user verb, never inferred. The
dispatcher checks this gate FIRST, before seat/CAS/ledger/delivery.
"""

import re

ACTION_PATTERNS = {
    "send": [r"\bsend\b", r"\bemail (it|this|them) to\b", r"\bdm\b"],
    "publish": [r"\bpublish\b", r"\bpost (it|this) (to|on)\b", r"\bdeploy to prod",
                r"\bpush live\b"],
    "spend": [r"\bspend\b", r"\bbuy\b", r"\bpay\b", r"\bcharge\b",
              r"\bsubscribe\b"],
    "delete": [r"\bdelete\b", r"\bdrop (the )?(table|db|database)\b",
               r"\brm -rf\b", r"\bremove (all|everything)\b"],
    "production-write": [r"\bproduction\b.*\b(write|update|delete|migrate)\b",
                         r"\bmigrate\b", r"\btruncate\b"],
    "external-write": [r"\bwebhook\b", r"\bapi (call|post|write)\b",
                       r"\bexternal\b.*\b(write|post|push)\b",
                       r"\btransfer\b"],
}

_COMPILED = {cls: [re.compile(p, re.IGNORECASE) for p in pats]
             for cls, pats in ACTION_PATTERNS.items()}


def classify_action(text):
    """Return action class name or None."""
    for cls, patterns in _COMPILED.items():
        for pat in patterns:
            if pat.search(text or ""):
                return cls
    return None


def check(message, decision=None):
    """Return ('ALLOW', None) or ('APPROVAL_REQUIRED', {reason, action_class}).

    Any irreversible-class signal in the message text forces
    APPROVAL_REQUIRED regardless of the route decision kind.
    """
    action = classify_action(message.get("text", ""))
    if action is None:
        return "ALLOW", None
    reason = ("irreversible action class '%s' requires explicit approval; "
              "default deny, never auto-delivered" % action)
    return "APPROVAL_REQUIRED", {"reason": reason[:280],
                                 "action_class": action}
