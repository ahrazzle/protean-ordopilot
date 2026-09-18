"""Model policy: explicit-config tier precedence + fallback recording.

Precedence (explicit config only, never silent substitution):
  local-configured > free (gated) > cheap-hosted > main-model.

The `free` tier exists in the enum but is DISABLED unless explicitly
configured AND free_tier_allowed:true AND verified at startup (verified
flag). No silent substitution: on timeout/error the next tier is tried and
`fallback_from` is recorded; total outage -> ESCALATE provider-unavailable.
No secrets are stored here — provider/model names only.
"""

from . import ROUTER_CONFIDENCE_FLOOR, ROUTER_TIMEOUT_S

TIER_LOCAL = "local-configured"
TIER_FREE = "free"  # gated: configured + allowed + verified, else skipped
TIER_CHEAP = "cheap-hosted"
TIER_MAIN = "main-model"

TIER_ORDER = (TIER_LOCAL, TIER_FREE, TIER_CHEAP, TIER_MAIN)


class PolicyExhausted(Exception):
    pass


class ModelConfig:
    def __init__(self, router=None, main=None, local=None, free=None,
                 cheap=None, free_tier_allowed=False, free_verified=False,
                 timeout_s=ROUTER_TIMEOUT_S,
                 confidence_floor=ROUTER_CONFIDENCE_FLOOR):
        # Each tier: {provider, model} or None (= disabled, never defaulted).
        self.router = router
        self.main = main
        self.local = local
        self.free = free
        self.cheap = cheap
        self.free_tier_allowed = bool(free_tier_allowed)
        self.free_verified = bool(free_verified)
        self.timeout_s = float(timeout_s)
        self.confidence_floor = float(confidence_floor)

    @classmethod
    def from_dict(cls, d):
        d = dict(d or {})

        def tier(key):
            v = d.get(key)
            if not v:
                return None
            if not (v.get("provider") and v.get("model")):
                raise ValueError("tier '%s' needs provider+model" % key)
            return {"provider": v["provider"], "model": v["model"]}

        return cls(router=tier("router"), main=tier("main"),
                   local=tier("local"), free=tier("free"),
                   cheap=tier("cheap"),
                   free_tier_allowed=d.get("free_tier_allowed", False),
                   free_verified=d.get("free_verified", False),
                   timeout_s=d.get("timeout_s", ROUTER_TIMEOUT_S),
                   confidence_floor=d.get("confidence_floor",
                                          ROUTER_CONFIDENCE_FLOOR))


def free_tier_enabled(config):
    return bool(config.free and config.free_tier_allowed
                and config.free_verified)


def resolve_chain(config, role="router"):
    """Ordered [(tier, provider, model)] for role in {router, main}.

    The pinned tier for the role (if configured) always comes first, then
    the shared fallback ladder. The router never borrows the main tier
    implicitly: main appears only as the last-resort fallback entry.
    """
    chain = []
    pinned = getattr(config, role, None)
    if pinned:
        chain.append(("%s-pinned" % role, pinned["provider"],
                      pinned["model"]))
    for tier_name, tier in ((TIER_LOCAL, config.local),
                            (TIER_CHEAP, config.cheap),
                            (TIER_MAIN, config.main)):
        if tier and not any(p == tier["provider"] and m == tier["model"]
                            for _, p, m in chain):
            chain.append((tier_name, tier["provider"], tier["model"]))
    if config.free and free_tier_enabled(config):
        chain.insert(1 if chain else 0,
                     (TIER_FREE, config.free["provider"],
                      config.free["model"]))
    return chain


def call_with_fallback(config, call_fn, role="router"):
    """Try tiers in order. call_fn(provider, model) may raise (timeout etc).

    Returns (result, provider, model, fallback_from|None). Raises
    PolicyExhausted when no tier is available or all fail."""
    chain = resolve_chain(config, role)
    if not chain:
        raise PolicyExhausted("no tiers configured for role '%s'" % role)
    first = chain[0][0]
    last_err = None
    for tier_name, provider, model in chain:
        try:
            return (call_fn(provider, model), provider, model,
                    None if tier_name == first else
                    {"tier": first, "error": str(last_err)})
        except Exception as e:  # noqa: BLE001 — any tier failure falls over
            last_err = e
            continue
    raise PolicyExhausted("all tiers failed for role '%s': %s"
                          % (role, last_err))


def escalate_unavailable(role="router", route_depth=0):
    """Terminal ESCALATE decision for total provider outage."""
    return {
        "kind": "ESCALATE",
        "target_session_id": None,
        "target_slug": None,
        "reason": "provider-unavailable: no %s tier reachable" % role,
        "confidence": 0.0,
        "required_context": [],
        "provider": "policy",
        "model": "unavailable",
        "router_latency_ms": 0,
        "route_depth": int(route_depth),
    }
