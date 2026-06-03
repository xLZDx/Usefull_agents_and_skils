#!/usr/bin/env python3
"""PreToolUse gate for the Agent (subagent spawn) tool.

Mechanically enforces the agent-spawn HARD GATE from CLAUDE.md:
  "spawning >3 heavy agents in one message without an announced tier + recon
   in that SAME message is forbidden."

Behavior:
  - Counts HEAVY agent spawns in a rolling 30s window (proxy for "one turn/burst").
  - A spawn is LIGHT (not counted) when its EFFECTIVE model is haiku. An explicit
    model override is authoritative (light iff it contains 'haiku'); with no
    override, the 4 Tier-C classifiers count as light (frontmatter haiku). A
    Tier-C agent forced onto a heavy model (e.g. model=opus) is HEAVY -- this
    closes the name-based exemption hole. Everything else is HEAVY.
  - On the 4th+ heavy spawn in the window, DENY -- UNLESS the sentinel
    data/agent_review/tier_ack.json exists and is younger than 120s (the session
    writes it when it announces a confirmed T4 tier + recon).

Safety:
  - FAIL-OPEN. Any error -> exit 0 with no output (tool proceeds). A hook bug must
    never block legitimate work.
  - State + sentinel live under <project>/data/agent_review/ (resolved from this
    file's location, always on D:, never C:).
  - State written atomically (temp + os.replace). ASCII only.
"""

import sys
import os
import json
import time
import tempfile
from pathlib import Path

WINDOW_S = 30.0          # rolling window that approximates "one turn / burst"
HEAVY_LIMIT = 3          # >3 heavy spawns in the window trips the gate
SENTINEL_MAX_AGE_S = 120.0   # tier_ack.json must be this fresh to exempt

# Tier-C classifiers running on Haiku (token-opt 2026-05-23). Cheap -> not counted.
HAIKU_AGENTS = frozenset({
    "comment-analyzer",
    "opensource-sanitizer",
    "pr-test-analyzer",
    "refactor-cleaner",
})


def _state_dir():
    # tools/hooks/agent_spawn_gate.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2] / "data" / "agent_review"


def _allow():
    # No output + exit 0 == hook does not object; tool proceeds.
    sys.exit(0)


def _deny(reason):
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)


def _is_light(tool_input):
    # An explicit model override is authoritative: light iff it is a haiku.
    # This closes the hole where a Tier-C agent forced onto a heavy model
    # (e.g. model=opus) would otherwise be exempt by name.
    model = str(tool_input.get("model", "") or "").strip().lower()
    if model:
        return "haiku" in model
    # No override -> the 4 Tier-C classifiers run on haiku per their frontmatter.
    subagent = str(tool_input.get("subagent_type", "") or "").strip().lower()
    return subagent in HAIKU_AGENTS


def _atomic_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".spawn_window_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="ascii") as fh:
            json.dump(obj, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def main():
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}

    if data.get("tool_name") != "Agent":
        _allow()

    tool_input = data.get("tool_input") or {}
    if _is_light(tool_input):
        _allow()

    now = time.time()
    state_dir = _state_dir()
    window_path = state_dir / "spawn_window.json"

    # Load + prune the rolling window.
    recent = []
    try:
        if window_path.exists():
            prev = json.loads(window_path.read_text(encoding="ascii"))
            recent = [float(t) for t in prev.get("ts", []) if (now - float(t)) < WINDOW_S]
    except (OSError, ValueError, TypeError):
        recent = []

    recent.append(now)
    try:
        _atomic_write_json(window_path, {"ts": recent})
    except OSError:
        pass  # fail-open: counting still works for this invocation

    if len(recent) <= HEAVY_LIMIT:
        _allow()

    # 4th+ heavy spawn in the window -> check the tier-ack sentinel.
    sentinel = state_dir / "tier_ack.json"
    try:
        if sentinel.exists() and (now - sentinel.stat().st_mtime) < SENTINEL_MAX_AGE_S:
            _allow()
    except OSError:
        _allow()  # fail-open if we cannot stat the sentinel

    subagent = str(tool_input.get("subagent_type", "") or "").strip() or "<unknown>"
    _deny(
        "HARD GATE (CLAUDE.md Multi-Agent Consensus): this is the "
        + str(len(recent))
        + "th heavy agent spawn within "
        + str(int(WINDOW_S))
        + "s (agent='"
        + subagent
        + "'). Spawning >"
        + str(HEAVY_LIMIT)
        + " heavy agents at once without an announced tier + recon is forbidden "
        + "(burn incident 2026-06-03: 6 agents ~= 1.1M tokens). To proceed for a "
        + "genuine T4 plan: run code-explorer recon first, announce the tier, then "
        + "touch data/agent_review/tier_ack.json (valid 120s) and re-spawn. "
        + "Otherwise default to the TIER table (T2=3 / T3=5-7) and spawn <=3."
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        # Absolute fail-open: never block a tool because the gate itself errored.
        sys.exit(0)
