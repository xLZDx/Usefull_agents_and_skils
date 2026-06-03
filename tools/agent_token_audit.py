"""Agent token audit — Phase 0 baseline measurement.

Walks ~/.claude/agents/*.md and ~/.claude/skills/*/SKILL.md, estimates
token cost per spawn / invocation / main-context turn, emits a JSON
baseline for before/after comparison across the Token Optimization Plan
v1.1 phases.

Method: chars/4 heuristic. Not exact tiktoken counts, but consistent
across runs — the relative deltas before vs after are what matter.

Usage:
    python tools/agent_token_audit.py --out data/agent_baseline_<date>.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Approximate tokens per tool JSONSchema injection (observed harness output,
# updated 2026-05-23). Update if Claude Code harness version changes.
TOOL_SCHEMA_TOKENS = {
    "Read": 500,
    "Write": 600,
    "Edit": 700,
    "Bash": 2000,
    "Grep": 400,
    "Glob": 300,
    "WebFetch": 400,
    "WebSearch": 300,
    "Task": 800,
    "TodoWrite": 600,
    "NotebookEdit": 700,
}

CHARS_PER_TOKEN = 4.0

AGENTS_DIR = Path.home() / ".claude" / "agents"
SKILLS_DIR = Path.home() / ".claude" / "skills"


def estimate_tokens(text: str) -> int:
    return int(round(len(text) / CHARS_PER_TOKEN))


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    fm_text, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, body.strip()


def extract_tools(tools_raw: str) -> list[str]:
    return re.findall(r"[A-Za-z_]+", tools_raw or "")


def audit_agent(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    description = fm.get("description", "")
    model = fm.get("model", "sonnet")
    tools = extract_tools(fm.get("tools", ""))
    tools_tokens = sum(TOOL_SCHEMA_TOKENS.get(t, 400) for t in tools)
    body_tokens = estimate_tokens(body)
    desc_tokens = estimate_tokens(description)
    return {
        "name": fm.get("name", path.stem),
        "path": str(path),
        "model": model,
        "tools": tools,
        "body_chars": len(body),
        "body_tokens_est": body_tokens,
        "description_chars": len(description),
        "description_tokens_est": desc_tokens,
        "tools_tokens_est": tools_tokens,
        "total_per_spawn_tokens_est": body_tokens + tools_tokens,
    }


def audit_skill(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    description = fm.get("description", "")
    body_tokens = estimate_tokens(body)
    desc_tokens = estimate_tokens(description)
    return {
        "name": fm.get("name", path.parent.name),
        "path": str(path),
        "body_chars": len(body),
        "body_tokens_est": body_tokens,
        "description_chars": len(description),
        "description_tokens_est": desc_tokens,
        "total_per_invocation_tokens_est": body_tokens,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if not AGENTS_DIR.exists():
        print(f"ERROR: {AGENTS_DIR} not found", file=sys.stderr)
        return 1
    if not SKILLS_DIR.exists():
        print(f"ERROR: {SKILLS_DIR} not found", file=sys.stderr)
        return 1

    agents: dict[str, dict[str, Any]] = {}
    for f in sorted(AGENTS_DIR.glob("*.md")):
        a = audit_agent(f)
        agents[a["name"]] = a

    skills: dict[str, dict[str, Any]] = {}
    for f in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        s = audit_skill(f)
        skills[s["name"]] = s

    body_tokens_list = [a["body_tokens_est"] for a in agents.values()]
    total_desc_tokens = sum(a["description_tokens_est"] for a in agents.values())
    avg_body = sum(body_tokens_list) / max(1, len(body_tokens_list))
    max_body = max(body_tokens_list) if body_tokens_list else 0
    max_name = max(agents.values(), key=lambda a: a["body_tokens_est"])["name"] if agents else ""

    sorted_bodies = sorted(body_tokens_list, reverse=True)
    typical_15 = sum(sorted_bodies[:15])

    sorted_spawn = sorted(agents.values(), key=lambda a: a["total_per_spawn_tokens_est"], reverse=True)
    top10_spawn = sum(a["total_per_spawn_tokens_est"] for a in sorted_spawn[:10])

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": f"chars/{CHARS_PER_TOKEN} heuristic",
        "tools_token_estimates": TOOL_SCHEMA_TOKENS,
        "agents": agents,
        "skills": skills,
        "aggregates": {
            "agents_count": len(agents),
            "skills_count": len(skills),
            "total_descriptions_tokens_est": total_desc_tokens,
            "main_context_overhead_per_turn_tokens": total_desc_tokens,
            "avg_agent_body_tokens": round(avg_body),
            "max_agent_body_tokens": max_body,
            "max_agent_name": max_name,
            "estimated_t4_round1_top15_body_tokens": typical_15,
            "estimated_t4_round1_top10_full_spawn_tokens": top10_spawn,
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Agents:                                 {len(agents)}")
    print(f"Skills:                                 {len(skills)}")
    print(f"Main context overhead (descriptions):   ~{total_desc_tokens} tokens / turn")
    print(f"Avg agent body:                         ~{int(avg_body)} tokens")
    print(f"Max agent body:                          {max_body} tokens ({max_name})")
    print(f"Est. T4 round 1 top-15 body only:       ~{typical_15} tokens")
    print(f"Est. T4 round 1 top-10 body+tools:      ~{top10_spawn} tokens")
    print(f"\nBaseline written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
