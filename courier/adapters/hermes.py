"""Thin Hermes adapter: CLI wrapper + gateway hook shape.

Two integration paths (per adjudicated OPEN-1):

1. `hermes_cli` wrapper: subprocess calls to `hermes chat --oneshot
   --resume <id>` for continuation and `hermes sessions ...` for lookup.
   No new API, but pays process spawn and loses hook context.
2. `pre_gateway_dispatch` hook module: `pre_gateway_dispatch(event)`
   observer/rewriter fired per incoming MessageEvent BEFORE auth/pairing
   (gateway/run_inbound.py). Return {"action": "skip"} to drop,
   {"action": "rewrite", "text": ...} to replace text, or
   {"action": "allow"} / None for normal dispatch. Ships as the optional,
   documented integration path.

Verified facts used here (hazen-research.md): resume-by-id contract
(`--resume`, unknown id RAISES, compression-chain redirect, stored session
runtime restored unless --model explicit); `register_cli_command` +
`register_hook("pre_gateway_dispatch")` plugin surface; second cheap model
via `model_aliases` direct alias or `delegation:` block; local models via
`custom` provider + base_url (opt-in, never auto-started).

HONEST UNKNOWNS (research-marked, adapter stays pluggable — core never
imports Hermes internals):
- UNKNOWN whether `pre_gateway_dispatch` fires for CLI-local turns or only
  gateway platform events (fire-site is GatewayInboundMixin; CLI path not
  traced). If it does not fire for CLI-local turns, use path 1 (wrapper).
- UNKNOWN `pre_gateway_dispatch` latency budget / timeout on slow hooks.
  Keep hook work bounded (classify-only, no network fan-out).
- UNKNOWN per-channel -> profile binding contract (profile_channels.py
  unread). Multi-profile routing keys are passed through opaquely.
- UNKNOWN concurrent-resume locking under two writers and exact
  `assert_resume_safe` rejection conditions. Courier's own seat/CAS still
  guards Courier-side writes; treat Hermes-side races as escalate+retry.
- UNKNOWN standalone public sessions REST/SDK doc page; the verified
  programmatic path is in-process SessionDB + CLI verbs.
- UNKNOWN Nous Portal free-model/trial path (subscription-only per docs).
  The `free` policy tier stays disabled unless explicitly configured AND
  verified — never assume a Portal free path here.
"""

import shutil
import subprocess

HOOK_NAME = "pre_gateway_dispatch"


def hermes_available():
    return shutil.which("hermes") is not None


def build_resume_command(session_id, prompt, model=None, extra_args=None):
    """argv for: hermes chat --oneshot --resume <id> [-m model] <prompt>."""
    cmd = ["hermes", "chat", "--oneshot", "--resume", str(session_id)]
    if model:
        cmd += ["-m", str(model)]
    cmd += list(extra_args or [])
    cmd.append(prompt)
    return cmd


def resume_via_cli(session_id, prompt, model=None, timeout_s=120):
    """One-shot continuation through the Hermes CLI. Returns
    {ok, returncode, stdout, stderr, argv}. Unknown ids raise upstream
    (never silently fork) — surfaced here as a nonzero returncode."""
    argv = build_resume_command(session_id, prompt, model=model)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout_s)
    except FileNotFoundError:
        return {"ok": False, "returncode": 127, "stdout": "",
                "stderr": "hermes CLI not found", "argv": argv}
    return {"ok": proc.returncode == 0, "returncode": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr, "argv": argv}


def build_sessions_list_command(json_output=True):
    argv = ["hermes", "sessions", "list"]
    if json_output:
        argv.append("--json")
    return argv


def pre_gateway_dispatch(event, route_fn=None):
    """Gateway hook shape. event: {text, platform, chat_id, ...}.

    route_fn(redacted_text) -> RouteDecision|None; when None, allow through
    untouched (observer mode). Returns allow/rewrite/skip dicts.
    NOTE: unverified whether this fires for CLI-local turns (see UNKNOWNS).
    """
    text = (event or {}).get("text", "")
    if route_fn is None:
        return {"action": "allow"}
    try:
        decision = route_fn(text)
    except Exception:  # noqa: BLE001 — hook must never break dispatch
        return {"action": "allow"}
    if decision is None:
        return {"action": "allow"}
    kind = decision.get("kind")
    if kind == "ESCALATE":
        return {"action": "allow",
                "courier": {"parked": True,
                         "reason": decision.get("reason", "")}}
    if kind in ("CONTINUE", "DIRECT") and decision.get("target_session_id"):
        return {"action": "rewrite", "text": text,
                "courier": {"resume": decision["target_session_id"],
                         "kind": kind}}
    return {"action": "allow", "courier": {"kind": kind}}


def register(ctx):
    """Hermes plugin entrypoint: register_cli_command for ops +
    register_hook(pre_gateway_dispatch). `ctx` is the host plugin context."""
    register_hook = getattr(ctx, "register_hook", None)
    if callable(register_hook):
        register_hook(HOOK_NAME, pre_gateway_dispatch)
    register_cmd = getattr(ctx, "register_cli_command", None)
    if callable(register_cmd):
        register_cmd("courier-route", "Route a message via Courier",
                     lambda args: {"ok": True})
    return {"hooks": [HOOK_NAME], "commands": ["courier-route"]}
