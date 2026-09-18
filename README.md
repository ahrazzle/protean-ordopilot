# Orda

## Names

- **Orda** — the product name users see. A quiet sorter for daily notes.
- **Ordapilot** — the internal implementation name (play on autopilot). The package and build work carry this name.
- **Protean / Proteus** — the underlying team system. Proteus adjudicates locked-decision changes and integrates lane work into the repo.

## What it is

Orda files each incoming note under the right project thread. It keeps one notebook per project. It carries short notes forward, not full transcripts. Sends, posts, spends, deletes, and shared-work writes wait for an explicit yes.

## Promise

You send notes in plain words. Orda files each one, recalls the gist without dragging the past along, asks when unsure, and never sends, spends, or erases without your yes.

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
courier doctor
courier topics
courier show <slug>
```

## Architecture

Spec: `leo-architecture.md` (_locked decisions, module map, data contracts, escalation ladder, test matrix — STABLE). Key points: stdlib-first `courier` package; Eldunari holds work state, Orda holds routing projection + delivery ledger; router output is exactly CONTINUE | NEW | DIRECT | HANDOFF | ESCALATE; redaction before any router call; approval gate default-deny on irreversible classes.

Hermes touchpoints (verified in Hermes v0.21.3 source): gateway `pre_gateway_dispatch` hook for intake plus a thin CLI wrapper (`hermes chat --resume <id>`). Dashboard and desktop plugins are real UI surfaces but not the message path.

## Status (honest)

Works in v0.1: intake → redact → router → dispatcher → catalog projection → ledger → approvals → compactor → policy → CLI verbs (`topics`, `show`, `correct`, `merge`, `split`, `pause`/`resume`, `forget`, `approvals`, `doctor`). Keyword topic matching over short summaries. CAS-guarded writes. Idempotent delivery. Fixed escalation ladder.

Later, not in v0.1: dashboard UI, auto topic-learning, embedding tier by default, ledger history compaction. UNKNOWN (unverified, do not rely on): per-channel profile binding, free-tier Portal path, concurrent-resume locking, sessions REST/SDK surface, hook latency budget, CLI-local hook firing, adapter binding choice, free-tier allowlist, embedding provider, clarification UX shape.

## License

MIT License — Copyright (c) 2026 Ahraz Arifuddin. See `LICENSE`.

STABLE
