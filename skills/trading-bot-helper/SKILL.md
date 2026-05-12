---
name: trading-bot-helper
description: Context loader template for an AI trading bot project. Customize paths under `<project-root>` for your own setup. Use when working with the trading engine, dashboard, training pipeline, ParquetClient/DuckDB, or any source under the project directory. Loads architecture, key file paths, training rules matrix, and operational defaults.
---

# AI Trading Bot — Skill Context (template)

This skill loads architectural truth for an AI trading bot project so you don't have to grep for it.

> Replace `<project-root>` with your own absolute path before use.

## Entry points
- Trading engine: `src/main.py`
- Dashboard (Flask, port 5000): `src/dashboard/app.py`
- Restart everything: `restart_all.ps1`
- Stop everything: `stop_all.ps1`

## Architecture
- **DB:** ParquetClient (DuckDB + partitioned Parquet on `data/db/`). File-based, no daemon.
- **Historical OHLCV:** served by `parquet_store.py` from `data/parquet/`.
- **State files:** all JSON I/O through `src/utils/safe_json.py` (filelock atomic writes).
- **Constants:** centralized in `src/utils/config.py`.
- **Execution model:** strictly sequential inside the bot loop — no parallelism.

## Defaults (do not override silently)
- **Testnet only** — never switch to Mainnet without explicit user instruction.
- DuckDB connections must set `temp_directory='<project-root>/data/cache/duckdb_temp'`.
- LLM fallback chain: keep the latest model first; update when newer models release.
- Bot is **personal use only** — never propose multi-tenant / public onboarding features. Goal: profit + capital preservation for the operator.

## Training pipeline
- Cluster orchestrator: port 7700 (`src/server/control_plane.py` or similar).
- 4 lane agents per the cluster-routed training plan (`core/PHASE_100_CLUSTER_ROUTED_TRAINING.md`).
- Model × TF coverage matrix in `data/training_rules.json` — READ ON EVERY TRAINING STARTUP. Source of truth for which (model, timeframe) cells are applicable / experimental / skip.
- Worker laptop launcher: `<worker-launcher-path>` (hardened with taskkill /F /T + WMI verify + port fallback).
- Worker SMB mount via account configured outside this repo.
- Single-instance lock: `data/train_all_models.lock`.

## Tests
- `tests/test_dashboard.py` is the canonical regression suite. 0 failures gates every push.
- After every code change, add/update assertions and verify 0 failures.

## Logs & monitoring
- `logs/trading.log` — main runtime log.
- `data/process_deaths.json`, `data/process_ids.json` — process supervisor state.
- `data/training_status_report.json`, `data/training_sweep_watchdog_state.json` — training pipeline state.
- `/api/monitor/services` on the dashboard for live health.
- `/api/monitor/health` for aggregate up/down.
- `/api/strategy/full` for ML model summary.

## Key plans (read in this order for full context)
1. `PLAN_<date>_outstanding.md` — priority-ordered roadmap.
2. `core/PHASE_100_CLUSTER_ROUTED_TRAINING.md` — current training architecture.
3. `core/SPRINT_1A_PER_MODEL_AGENTS_AND_KPI.md` — per-model agent refactor + KPI gate.
4. `TECH_IMPLEMENTATION_PLAN_<date>.md` — file-level plan for hardening sprints.
5. `COMPETITIVE_ASSESSMENT_<date>.md` — feature roadmap.

## Inherits global rules
This project inherits rules from `<workspace-root>/CLAUDE.md` (approval gate, no-guessing, regression tests, disk policy, git lifecycle including todo-in-commits).
