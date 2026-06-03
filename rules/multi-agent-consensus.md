# Multi-Agent Review & Consensus (with cost-aware tiering)

For architectural / multi-phase / multi-file plans, spawn specialist agents to review BEFORE presenting to the operator, iterate to consensus, then present only the post-consensus plan.

## Four load-bearing behaviors

1. **Mandatory for risky/non-trivial changes.** Multi-file changes, new modules, security/auth/SQL/secrets surfaces, architectural decisions, deletions -> specialist review before writing and after completion. Trivial (typo / 1-line config / comment) does not.
2. **No permission needed to run review agents.** Reviews are READ-ONLY and pre-approved. Auto-trigger; never ask "should I run agents?".
3. **Consensus is presented AFTER review, not before.** The operator sees ONLY the post-consensus plan + audit trail (full roster, round-by-round findings, resolutions). The initial pre-review draft is internal scaffolding.
4. **Operator implementation-GO is still required before implementation.** Auto-approved review does NOT authorise building code.

## Recon-first tiering (the SINGLE entry — caps the agent count)

Classify the plan BEFORE spawning. Announce tier + estimated calls + planned rounds upfront; operator silence = auto-go (override window is BEFORE spawn or via interrupt).

| Tier | Trigger | Agents | Rounds |
|---|---|---|---|
| T1 | typo / 1-line / comment | 0 | 0 |
| T2 | single-file logic | 3 | 1 |
| T3 | multi-file feature (3-5 files) | 5-7 | 1-2 |
| T4 | architectural / ML / risk / governance | 10-15 | up to 4 |

- **Recon-first (T3/T4):** one `code-explorer` pass enumerates real files + domains BEFORE triage -> cuts 30-50% of just-in-case agents.
- **The full roster is a RELEVANCE MAP, not a spawn-all.** Walk the agent list only to decide who is relevant; the TIER caps how many actually spawn. Floors (8+ for a 5-phase plan, 12-15 for ML/risk) apply ONLY inside an already-confirmed T4, AFTER recon — never as a default.
- **HARD GATE:** spawning >3 heavy agents in one message without an announced tier + recon in that SAME message is forbidden. An unclassified plan defaults to T2=3 / T3=5-7, not the floors. This is enforced mechanically by `hooks/agent_spawn_gate.py`.

## Consensus loop (T4)

Round 1 Discovery (parallel; BLOCKER/MAJOR/MINOR/NIT) -> Round 2 Cross-Review (each agent AGREE/DISAGREE/REFINE on every peer finding + NEW) -> Round 3+ Convergence (narrow respawn on contested + new). Stop when all "consensus reached" AND no new BLOCKER/MAJOR AND zero DISAGREE; hard 4-round circuit breaker.

**Skip round 2** when round 1 = 0 BLOCKER + <=2 MAJOR + no overlap (covers ~60% of plans). Use the `agent-consensus` skill to standardise the artifact.

## Empiricism over poetry

Show ALL agent output. Cross-check every load-bearing finding against the cited `file:line` — if the code doesn't match the claim, it's a confabulation: label it and dismiss. Reject "poetry" findings (no concrete bug, no cited line). Promote facts / best-practice / blockers.
