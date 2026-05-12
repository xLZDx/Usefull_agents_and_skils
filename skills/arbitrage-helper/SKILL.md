---
name: arbitrage-helper
description: Context loader template for a CEX-DEX statistical arbitrage project. Customize paths under `<project-root>` for your own setup. Use when working on CEX ↔ L2 DEX bots, the arbitrage tab in a trading dashboard, HALT flag, risk gates, or any source under the project directory.
---

# arbitrage_strategy — Skill Context (template)

This skill loads architectural truth for a CEX-DEX arbitrage project so you don't have to grep for it.

> Replace `<project-root>` with your own absolute path before use.

## Scope
- CEX-DEX statistical arbitrage: e.g. Bybit Spot ↔ Base L2 DEX.
- Pilot pairs: BTC/USDT, ETH/USDT, SOL/USDT.
- Bankroll stub: $500/side until ramp phase.
- Default mode: **SHADOW**. TESTNET via env var. Mainnet flag separate and gated.

## Layout
- Working directory: `<project-root>`
- Sister project (path-editable dep, optional): `<sister-project-root>`
- Python venv: `venv\` (separate from sister project)
- Dashboard: shared with trading bot at port 5000, "Arbitrage" tab + `/api/arb/*` namespace
- Plan source of truth: `core/PLAN.md` — update when scope changes
- Logs: `logs/arb_<service>_<date>.jsonl`, daily rotation
- DuckDB temp dir: `data/arb/cache/duckdb_temp/`
- Secrets: `.env` (never committed), `.env.example` for templates

## Risk Defaults (MANDATORY)
- **HALT file flag:** `data/arb/HALT` — every execution path checks within ≤2s.
- **Daily loss cap:** 5% of `BANKROLL_PER_SIDE_USD`.
- **Per-trade cap:** 10% of `BANKROLL_PER_SIDE_USD`.
- **Withdrawal-disabled flag** is checked before any CEX balance change.
- All DEX swaps require `amountOutMin` + `deadline`.
- All on-chain sends go through bundle simulation first.

## Tests
- `tests/test_arb_<phase>.py` mirroring trading-bot pattern.
- 0 failures gate every push.
- Restart system after each code change with `restart_all.ps1` so live system reflects latest code.

## Inherits global rules
This project inherits rules from `<workspace-root>/CLAUDE.md` (approval gate, no-guessing, regression tests, disk policy, git lifecycle including todo-in-commits, functional tests prove behavior).
