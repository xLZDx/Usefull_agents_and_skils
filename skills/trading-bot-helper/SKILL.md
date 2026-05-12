---
name: trading-bot-helper
description: Context loader for the AI Trading Assistance project at D:\test 2\AI trading assistance. Use when working with the trading engine, dashboard, training pipeline, ParquetClient/DuckDB, or any source under that directory. Loads architecture, key file paths, training rules matrix, and operational defaults.
---

# AI Trading Assistance — Skill Context

This skill loads the project's architectural truth so you don't have to grep for it.

## Entry points
- Trading engine: `src/main.py`
- Dashboard (Flask, port 5000): `src/dashboard/app.py`
- Restart everything: `restart_all.ps1`
- Stop everything: `stop_all.ps1`

## Architecture
- **DB:** ParquetClient (DuckDB + partitioned Parquet on `data/db/`). File-based, no daemon. Replaces QuestDB after Phase 1–5 migration.
- **Historical OHLCV:** 48 GB served by `parquet_store.py` from `data/parquet/`.
- **State files:** all JSON I/O through `src/utils/safe_json.py` (filelock atomic writes).
- **Constants:** centralized in `src/utils/config.py`.
- **Execution model:** strictly sequential inside the bot loop — no parallelism.

## Defaults (do not override silently)
- **Testnet only** — never switch to Mainnet without explicit user instruction.
- DuckDB connections must set `temp_directory='D:/test 2/AI trading assistance/data/cache/duckdb_temp'`.
- Gemini fallback chain starts with `gemini-3.1-pro-preview`. Update when a newer model releases.
- Bot is **personal use only** — never propose Stripe / marketplace / multi-tenant / public onboarding features. Goal: profit + capital preservation FOR THE OPERATOR.

## Training pipeline
- Cluster orchestrator: port 7700 (`src/server/control_plane.py` or similar).
- 4 lane agents per Phase 100 plan (`core/PHASE_100_CLUSTER_ROUTED_TRAINING.md`).
- Model × TF coverage matrix in `data/training_rules.json` — READ ON EVERY TRAINING STARTUP. Source of truth for which (model, timeframe) cells are applicable / experimental / skip.
- Worker laptop "Ivan" launcher: `C:\ai-worker\restart_workers.ps1` (canonical restart, hardened with taskkill /F /T + WMI verify + port fallback). This is the documented harness-imposed C:-drive bridge — all data + logs the worker produces still land on D:.
- Worker SMB mount via `MicrosoftAccount\<email>`.
- Single-instance lock: `data/train_all_models.lock` (Phase 97).

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
1. `PLAN_2026_05_08_outstanding.md` — priority-ordered roadmap; P0 retrain gaps → P3 perf.
2. `core/PHASE_100_CLUSTER_ROUTED_TRAINING.md` — current training architecture.
3. `core/SPRINT_1A_PER_MODEL_AGENTS_AND_KPI.md` — per-model agent refactor + KPI gate.
4. `TECH_IMPLEMENTATION_PLAN_2026-05-10.md` — file-level plan for Sprint 0 / 0a / 0b / 0c hardening.
5. `COMPETITIVE_ASSESSMENT_2026-05-10_v2.md` — 48-item roadmap, heavily pruned by the personal-use reframe.

## Inherits global rules
This project inherits all rules from `D:\test 2\CLAUDE.md` (approval gate, no-guessing, regression tests, D:-drive-only, git lifecycle including todo-in-commits).
