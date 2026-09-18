"""Orda router-core package (v0.1, CLI-core MVP).

Routing projection + delivery ledger only. Canonical work state lives in
Eldunari; this package never forks it.
"""

__version__ = "0.1.0"

# Named constants (frozen defaults; overridable only via explicit config file).
ROUTER_TIMEOUT_S = 8.0
ROUTER_RETRY_ONCE = True
ROUTER_CONFIDENCE_FLOOR = 0.65
AMBIGUOUS_MARGIN = 0.10
MAX_ROUTE_DEPTH = 4
HANDOFF_BUDGET_CHARS = 2000
SESSION_SUMMARY_BUDGET_CHARS = 500
TOPIC_SEARCH_K = 5
SEAT_TTL_S = 600

# CLI exit codes (mirror Eldunari).
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONFLICT = 3
EXIT_LEASE = 4
EXIT_INTEGRITY = 5

DECISION_KINDS = ("CONTINUE", "NEW", "DIRECT", "HANDOFF", "ESCALATE")

DISPATCH_RESULTS = (
    "delivered",
    "duplicate-ack",
    "held-for-approval",
    "escalated",
    "parked-busy",
    "parked-clarification",
)
