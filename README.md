# Orda

## Names

- **Orda** — the product name users see. One plain input for getting work done with AI.
- **Ordapilot** — the internal implementation name (play on autopilot). The package and build work carry this name.
- **Protean / Proteus** — the underlying team system. Proteus adjudicates locked-decision changes and integrates lane work into the repo.

## What it is

One input for getting work done. You type what you want in plain words and press send. Orda works out what kind of request it is and handles it, then gives you the result. The backend shipped in this repository is a stand-in. It records the request and returns a fixed shape to show the interface rather than to produce model output. A live backend does that work in production. You do not manage anything. Sends, posts, spends, deletes, and shared-work writes wait for an explicit yes.

## Promise

Type what you want in plain words. Orda reads the request, does the work, and gives you the result. In this repository the result comes from the stand-in. It is a fixed shape that shows where a live model result would appear, not the model output itself. It asks when a request could mean two things, and it never sends, spends, or erases without your yes.

## Quick start

```sh
git clone <repo-url>
cd protean-ordopilot
pip install -e .
```

Run the checks (12 test classes: continuation, new-topic, ambiguous, escalation, compression, idempotency, busy/expired seats, CAS conflict, provider fallback, redaction, irreversible boundary, CLI path):

```sh
pytest
```

Try the CLI demo against the in-process fake backend (no Hermes needed):

```sh
orda doctor
orda topics
orda show <slug>
```

## Architecture

Spec: `leo-architecture.md` (_locked decisions, module map, data contracts, escalation ladder, test matrix — STABLE). Key points: stdlib-first `orda` package; Eldunari holds work state, Orda holds routing projection + delivery ledger; router output is exactly CONTINUE | NEW | DIRECT | HANDOFF | ESCALATE; redaction before any router call; approval gate default-deny on irreversible classes.

Hermes touchpoints (verified in Hermes v0.21.3 source): gateway `pre_gateway_dispatch` hook for intake plus a thin CLI wrapper (`hermes chat --resume <id>`). Dashboard and desktop plugins are real UI surfaces but not the message path.

## Status (honest)

Works in v0.1: intake → redact → router → dispatcher → catalog projection → ledger → approvals → compactor → policy → CLI verbs (`topics`, `show`, `correct`, `merge`, `split`, `pause`/`resume`, `forget`, `approvals`, `doctor`). Keyword topic matching over short summaries. CAS-guarded writes. Idempotent delivery. Fixed escalation ladder.

Later, not in v0.1: dashboard UI, auto topic-learning, embedding tier by default, ledger history compaction. UNKNOWN (unverified, do not rely on): per-channel profile binding, free-tier Portal path, concurrent-resume locking, sessions REST/SDK surface, hook latency budget, CLI-local hook firing, adapter binding choice, free-tier allowlist, embedding provider, clarification UX shape.

## License

MIT License — Copyright (c) 2026 Ahraz Arifuddin. See `LICENSE`.

STABLE
