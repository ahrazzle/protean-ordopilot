# ADR-0001: Why a router layer at intake

Status: accepted (Leo, STABLE).
Date: 2026-09-18.

## Context

Users juggle sessions manually (continue vs new vs handoff); misrouted
context wastes tokens and clobbers state (the TASK-HOME clobber failure in
the Eldunari ARCHITECTURE record).

## Decision

Put a small, cheap, bounded routing model at intake that classifies every
incoming message into CONTINUE / NEW / DIRECT / HANDOFF / ESCALATE, then a
deterministic dispatcher executes it under CAS + seat + idempotency +
approval gates.

## Rejected alternatives

(a) main-model-does-everything — correct but 10-50x cost/latency per
message and no deterministic idempotency/CAS envelope; (b) static
rules/regex router — brittle on ambiguous topics, no confidence signal,
unmaintainable keyword lists; (c) embedding-only retriever with no decision
record — retrieves but never decides, no provider/model audit, no approval
boundary; (d) second canonical work-state DB inside Orda — rejected, forks
Eldunari truth and reintroduces dual-write conflicts.

## Consequences

Extra hop (~t1 seconds, bounded) on every message; requires confidence
floor + escalation + ledger to stay safe; wins are invisible session
management with auditable decisions.

## Implementation (v0.1)

Deterministic rule engine as the default classifier (`courier/router.py`,
`courier/topics.py`); `RouterModel` interface for a pluggable small model
(test stub included, no network). Dispatcher (`courier/dispatcher.py`)
enforces approval gate first, then seat/CAS, ledger idempotency, deliver.
