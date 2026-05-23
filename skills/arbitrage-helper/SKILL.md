---
name: arbitrage-helper
description: Context loader for the arbitrage_strategy project at D:\test 2\arbitrage_strategy. Use when working on CEX-DEX statistical arbitrage, Bybit Spot ↔ Base L2 DEX bots, the arbitrage tab in the trading dashboard, HALT flag, risk gates, or any source under that directory. Loads risk defaults, plan source of truth, and key paths.
---

# arbitrage_strategy — Skill Context

This skill loads the project's architectural truth so you don't have to grep for it.

## Scope
- CEX-DEX statistical arbitrage: Bybit Spot ↔ Base L2 DEX.
- Pilot pairs: BTC/USDT, ETH/USDT, SOL/USDT.
- Bankroll stub: $500/side until Phase 12 ramp.
- Default mode: **SHADOW**. TESTNET via env var. Mainnet flag separate and gated.

## Layout
- Working directory: `D:\test 2\arbitrage_strategy`
- Sister project (path-editable dep): `D:\test 2\AI trading assistance`
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
- **Withdrawal-disabled flag** is checked before any Bybit balance change.
- All DEX swaps require `amountOutMin` + `deadline`.
- All on-chain sends go through bundle simulation first.

## Tests
- `tests/test_arb_<phase>.py` mirroring trading-bot pattern.
- 0 failures gate every push.
- Restart system after each code change with `restart_all.ps1` so live system reflects latest code.

## Inherits global rules
This project inherits all rules from `D:\test 2\CLAUDE.md` (approval gate, no-guessing, regression tests, D:-drive-only, git lifecycle including todo-in-commits, functional tests prove behavior).
