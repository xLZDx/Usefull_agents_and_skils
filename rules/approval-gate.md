# Approval Gate

No file writes, shell commands with side effects, code changes, or code-writing agent spawns may begin without an explicit operator **implementation GO**: the exact short command `GO` / `GO <gate-name>` (case-insensitive).

Casual approvals ("approved" / "go ahead" / "yes" / "ok" / "continue") do NOT release the gate. See `gate-based-development.md` for the two-GO model (implementation GO vs push GO).

## What triggers the gate (state-changing only)

- Writing, editing, or deleting files
- Running shell commands with side effects
- Spawning subagents that may write code
- Starting background processes
- API calls with side effects

## Pre-approved (never ask, never wait)

These are read-only / information-gathering and pre-approved at all times:

- **Multi-agent reviews** (read-only: Read/Grep/Glob/read-only Bash). Auto-trigger for non-trivial plans + after non-trivial commits per the tiering in `multi-agent-consensus.md`. The operator should NOT have to type "run agents".
- Read-only shell probes (ls, ps, git status, log tails, curl GET on read endpoints).
- Read / Grep / Glob / todo-list updates.

## What does NOT count as confirmation

Questions, requests for information, partial phrases ("sounds good", "ok", "да", "continue"), asking to save/plan/explain, or any message that does not contain the literal `GO`.

## Sub-steps are auto-approved

Once a plan is approved with an implementation GO, every layer/sub-step inside it proceeds without re-asking. The gate is on the PLAN boundary. New scope mid-conversation = un-approved; re-confirm.
