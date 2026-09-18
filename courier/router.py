"""Router: redacted Message + TopicCandidates + policy -> RouteDecision.

Output is exactly one of CONTINUE | NEW | DIRECT | HANDOFF | ESCALATE.
Pure w.r.t. state (no writes). Confidence in [0,1]; provider+model always
set. The deterministic rule engine is the default classifier; RouterModel
is the pluggable interface for a real small model (test stub included,
no network).
"""

import re
import time
import uuid
from datetime import datetime, timezone

from . import (AMBIGUOUS_MARGIN, MAX_ROUTE_DEPTH, ROUTER_CONFIDENCE_FLOOR)

PROVIDER_DETERMINISTIC = "deterministic"
MODEL_RULE_ENGINE = "rule-engine-v0"

DIRECT_RE = re.compile(
    r"(?:^|\b)(?:direct\s*:\s*|courier\s+send\s+)([\w][\w\-]*)\b", re.IGNORECASE)
HANDOFF_RE = re.compile(
    r"\b(?:handoff\s+to|move\s+(?:this|it|that)\s+to)\s+([\w][\w\-]*)\b",
    re.IGNORECASE)

# Below this candidate score the message is treated as novel (-> NEW);
# between here and the confidence floor it is unclear (-> ESCALATE).
NOVELTY_CEILING = 0.30


class RouterTimeout(Exception):
    pass


class RouterModel:
    """Pluggable classifier interface. classify() returns
    {kind, target_slug, confidence, reason, required_context} or raises
    RouterTimeout. It MUST receive redacted text only."""

    name = "base"

    def classify(self, redacted_text, candidates):
        raise NotImplementedError


class DeterministicRouter(RouterModel):
    """Default classifier: layered deterministic rules over candidates."""

    name = "deterministic"

    def classify(self, redacted_text, candidates):
        return rule_classify(redacted_text, candidates)


class StubRouterModel(RouterModel):
    """Scripted test double. script = list of dict-results or Exceptions."""

    name = "stub"

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def classify(self, redacted_text, candidates):
        self.calls.append({"text": redacted_text,
                           "candidates": list(candidates)})
        if not self.script:
            raise RouterTimeout("stub script exhausted")
        nxt = self.script.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return dict(nxt)


def _decision(kind, reason, confidence, target_session_id=None,
              target_slug=None, required_context=None, provider=None,
              model=None, route_depth=0, latency_ms=0):
    if kind not in ("CONTINUE", "NEW", "DIRECT", "HANDOFF", "ESCALATE"):
        raise ValueError("bad decision kind: %r" % kind)
    return {
        "kind": kind,
        "target_session_id": target_session_id,
        "target_slug": target_slug,
        "reason": str(reason)[:280],
        "confidence": max(0.0, min(1.0, float(confidence))),
        "required_context": list(required_context or []),
        "provider": provider or PROVIDER_DETERMINISTIC,
        "model": model or MODEL_RULE_ENGINE,
        "router_latency_ms": int(latency_ms),
        "route_depth": int(route_depth),
    }


def rule_classify(redacted_text, candidates, route_depth=0,
                  provider=None, model=None):
    """Core deterministic rules (also usable standalone)."""
    t0 = time.monotonic()
    lat = lambda: int((time.monotonic() - t0) * 1000)  # noqa: E731

    if route_depth > MAX_ROUTE_DEPTH:
        return _decision("ESCALATE", "route-depth-overflow: depth %d > %d"
                         % (route_depth, MAX_ROUTE_DEPTH), 0.5,
                         route_depth=route_depth, latency_ms=lat(),
                         provider=provider, model=model)

    m = DIRECT_RE.search(redacted_text)
    if m:
        slug = m.group(1).lower()
        tgt = next((c for c in candidates
                    if c["slug"].lower() == slug), None)
        return _decision("DIRECT", "explicit direct target '%s'" % slug,
                         0.95, tgt["session_id"] if tgt else None, slug,
                         [tgt["session_id"]] if tgt else [],
                         route_depth=route_depth, latency_ms=lat(),
                         provider=provider, model=model)

    m = HANDOFF_RE.search(redacted_text)
    if m:
        slug = m.group(1).lower()
        tgt = next((c for c in candidates
                    if c["slug"].lower() == slug), None)
        return _decision("HANDOFF", "explicit handoff to '%s'" % slug, 0.9,
                         tgt["session_id"] if tgt else None, slug,
                         [tgt["session_id"]] if tgt else [],
                         route_depth=route_depth, latency_ms=lat(),
                         provider=provider, model=model)

    if candidates and candidates[0].get("source") in (
            "explicit", "explicit-missing"):
        top = candidates[0]
        return _decision("CONTINUE", "explicit slug '%s'" % top["slug"], 1.0,
                         top["session_id"], top["slug"],
                         [top["session_id"]] if top["session_id"] else [],
                         route_depth=route_depth, latency_ms=lat(),
                         provider=provider, model=model)

    if not candidates:
        return _decision("NEW", "no topic candidates; novel message", 0.8,
                         "sess-" + uuid.uuid4().hex[:8], None, [],
                         route_depth=route_depth, latency_ms=lat(),
                         provider=provider, model=model)

    top = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    margin = top["score"] - second["score"] if second else 1.0
    if margin < AMBIGUOUS_MARGIN:
        names = ",".join(c["slug"] for c in candidates[:2])
        return _decision(
            "ESCALATE", "ambiguous-candidates: top2 within %.2f (%s)"
            % (AMBIGUOUS_MARGIN, names), round(top["score"], 4),
            None, None, [c["session_id"] for c in candidates[:2]
                         if c.get("session_id")],
            route_depth=route_depth, latency_ms=lat(),
            provider=provider, model=model)
    if top["score"] < NOVELTY_CEILING:
        return _decision("NEW", "novel message; best score %.2f < %.2f"
                         % (top["score"], NOVELTY_CEILING), 0.8,
                         "sess-" + uuid.uuid4().hex[:8], None, [],
                         route_depth=route_depth, latency_ms=lat(),
                         provider=provider, model=model)
    if top["score"] < ROUTER_CONFIDENCE_FLOOR:
        return _decision(
            "ESCALATE", "low-confidence: best %.2f < floor %.2f" %
            (top["score"], ROUTER_CONFIDENCE_FLOOR),
            round(top["score"], 4), None, None,
            [top["session_id"]] if top.get("session_id") else [],
            route_depth=route_depth, latency_ms=lat(),
            provider=provider, model=model)
    kind = "CONTINUE"
    return _decision(kind, "topic match '%s' via %s (%.2f)" %
                     (top["slug"], top.get("source", "?"), top["score"]),
                     round(top["score"], 4), top["session_id"], top["slug"],
                     [top["session_id"]] if top.get("session_id") else [],
                     route_depth=route_depth, latency_ms=lat(),
                     provider=provider, model=model)


def route(message, sessions, classifier=None, provider=None, model=None):
    """One-shot routing. message must be redacted (asserts _redacted)."""
    if not message.get("_redacted", False):
        raise ValueError("refusing to route unredacted message "
                         "(redact before any router call)")
    from .topics import rank_candidates
    cands = rank_candidates(message["text"], sessions)
    clf = classifier or DeterministicRouter()
    if isinstance(clf, DeterministicRouter):
        return rule_classify(message["text"], cands,
                             route_depth=message.get("route_depth", 0),
                             provider=provider, model=model)
    t0 = time.monotonic()
    res = clf.classify(message["text"], cands)
    lat = int((time.monotonic() - t0) * 1000)
    tgt = next((c for c in cands
                if c["slug"] == res.get("target_slug")), None)
    return _decision(res.get("kind", "ESCALATE"),
                     res.get("reason", "model decision")[:280],
                     res.get("confidence", 0.0),
                     tgt["session_id"] if tgt else None,
                     res.get("target_slug"),
                     res.get("required_context", []),
                     route_depth=message.get("route_depth", 0),
                     latency_ms=lat, provider=provider, model=model)


def _step(step, provider, model, latency_ms, confidence):
    return {"step": step, "provider": provider, "model": model,
            "latency_ms": int(latency_ms), "confidence": confidence,
            "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def route_with_escalation(message, sessions, classifier=None,
                          main_classifier=None,
                          provider="deterministic",
                          model="rule-engine-v0",
                          main_provider="main", main_model="main-model-v0"):
    """Fixed escalation ladder; every step recorded.

    1. small router (budget) -> 2. one retry into ambiguous bucket ->
    3. main model decides -> 4. user clarification. Returns
    (decision, steps).
    """
    from .topics import rank_candidates
    steps = []
    cands = rank_candidates(message["text"], sessions)
    clf = classifier or DeterministicRouter()

    def attempt(tag):
        t0 = time.monotonic()
        try:
            if isinstance(clf, DeterministicRouter):
                d = rule_classify(message["text"], cands,
                                  route_depth=message.get("route_depth", 0),
                                  provider=provider, model=model)
            else:
                r = clf.classify(message["text"], cands)
                tgt = next((c for c in cands
                            if c["slug"] == r.get("target_slug")), None)
                d = _decision(r.get("kind", "ESCALATE"),
                              r.get("reason", "model decision")[:280],
                              r.get("confidence", 0.0),
                              tgt["session_id"] if tgt else None,
                              r.get("target_slug"),
                              r.get("required_context", []),
                              route_depth=message.get("route_depth", 0),
                              latency_ms=int((time.monotonic() - t0) * 1000),
                              provider=provider, model=model)
            steps.append(_step(tag, provider, model, d["router_latency_ms"],
                               d["confidence"]))
            return d
        except RouterTimeout:
            steps.append(_step(tag, provider, model,
                               int((time.monotonic() - t0) * 1000), None))
            return None

    d = attempt("router-t1")
    if d is not None and d["reason"].startswith("route-depth-overflow"):
        return d, steps
    if d is not None and (d["kind"] != "ESCALATE" or
                          d["confidence"] >= ROUTER_CONFIDENCE_FLOOR):
        # Deterministic classifier already applied Layer C; accept unless it
        # explicitly escalated.
        if d["kind"] != "ESCALATE":
            return d, steps
    # Step 2: one retry with the ambiguous bucket (top-K + redacted text).
    d2 = attempt("router-retry")
    if d2 is not None and d2["kind"] != "ESCALATE":
        return d2, steps
    # Step 3: main model decides.
    t0 = time.monotonic()
    try:
        if main_classifier is not None:
            r = main_classifier.classify(message["text"], cands)
            tgt = next((c for c in cands
                        if c["slug"] == r.get("target_slug")), None)
            d3 = _decision(r.get("kind", "ESCALATE"),
                           r.get("reason", "main-model decision")[:280],
                           r.get("confidence", 0.0),
                           tgt["session_id"] if tgt else None,
                           r.get("target_slug"),
                           r.get("required_context", []),
                           route_depth=message.get("route_depth", 0),
                           latency_ms=int((time.monotonic() - t0) * 1000),
                           provider=main_provider, model=main_model)
        else:
            d3 = None
    except RouterTimeout:
        d3 = None
    steps.append(_step("main-model", main_provider, main_model,
                       int((time.monotonic() - t0) * 1000),
                       d3["confidence"] if d3 else None))
    if d3 is not None and d3["kind"] != "ESCALATE":
        return d3, steps
    # Step 4: user clarification — one bounded question, nothing auto-created.
    top2 = [c["slug"] for c in cands[:2]]
    q = ("Which topic did you mean? " + " / ".join(
        "'%s'" % s for s in top2)) if top2 else \
        "What topic is this? (no close matches found)"
    d4 = _decision("ESCALATE", ("clarification-needed: %s" % q)[:280], 0.0,
                   None, None,
                   [c["session_id"] for c in cands[:2]
                    if c.get("session_id")],
                   route_depth=message.get("route_depth", 0),
                   provider=main_provider, model=main_model)
    steps.append(_step("clarification", "user", "clarification", 0, None))
    return d4, steps
