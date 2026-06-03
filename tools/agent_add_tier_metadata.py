"""Phase 2.2 of Token Optimization Plan v1.1.

Adds `tier` + `token_budget_round1_words` + `token_budget_round_n_words`
to each agent's YAML frontmatter. Tier defines model class + output budget
match. Token budgets are advisory targets enforced via the Output Budget
block (Phase 1.3) for verbose agents; here we record the canonical numbers
in metadata so other tooling (skill, audit script, future Haiku migration)
can read them programmatically.

Tier definitions:
    A = critical reasoning / safety / domain-deep         (Sonnet/Opus, full budget)
    B = specialist reviewers                              (Sonnet today, Haiku candidate)
    C = classifiers (AGREE/DISAGREE pattern matchers)     (Haiku candidate, tight budget)
    D = formatters / operational / mechanical             (Haiku now, tightest budget)

Token budgets per tier (in words for round 1 / round N+):
    A: 600 / 250
    B: 500 / 200
    C: 350 / 150
    D: 250 / 100

Idempotent — re-running on already-tagged agents is a no-op.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENTS_DIR = Path.home() / ".claude" / "agents"
BACKUP_ROOT = Path.home() / ".claude" / "agent_backups"

TIER_MAP: dict[str, str] = {
    # Tier A — critical reasoning / safety-critical / domain-deep
    "architect": "A",
    "code-architect": "A",
    "crash-math-agent": "A",
    "database-reviewer": "A",
    "ml-engineer": "A",
    "performance-optimizer": "A",
    "planner": "A",
    "security-reviewer": "A",
    "silent-failure-hunter": "A",
    "training-inspector": "A",
    # Tier B — specialist reviewers
    "a11y-architect": "B",
    "build-error-resolver": "B",
    "code-explorer": "B",
    "code-reviewer": "B",
    "code-simplifier": "B",
    "cpp-build-resolver": "B",
    "cpp-reviewer": "B",
    "dart-build-resolver": "B",
    "e2e-runner": "B",
    "fastapi-reviewer": "B",
    "flutter-reviewer": "B",
    "harness-optimizer": "B",
    "network-config-reviewer": "B",
    "network-troubleshooter": "B",
    "python-reviewer": "B",
    "pytorch-build-resolver": "B",
    "seo-specialist": "B",
    "tdd-guide": "B",
    "type-design-analyzer": "B",
    # Tier C — classifiers (Haiku candidates)
    "comment-analyzer": "C",
    "opensource-sanitizer": "C",
    "pr-test-analyzer": "C",
    "refactor-cleaner": "C",
    # Tier D — formatters / operational / mechanical
    "conversation-analyzer": "D",
    "doc-updater": "D",
    "loop-operator": "D",
    "opensource-forker": "D",
    "opensource-packager": "D",
}

TIER_BUDGETS: dict[str, tuple[int, int]] = {
    "A": (600, 250),
    "B": (500, 200),
    "C": (350, 150),
    "D": (250, 100),
}


def parse_frontmatter(content: str) -> tuple[str, str, str]:
    m = re.match(r"^(---\r?\n)(.*?)(\r?\n---\r?\n)(.*)$", content, re.DOTALL)
    if not m:
        raise ValueError("no frontmatter found")
    return m.group(2), m.group(3) + m.group(4), m.group(1)


def upsert_field(fm_inner: str, key: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^({re.escape(key)}\s*:\s*)(.*)$", re.MULTILINE)
    if pattern.search(fm_inner):
        match = pattern.search(fm_inner)
        if match and match.group(2) == value:
            return fm_inner, False
        return pattern.sub(lambda m: m.group(1) + value, fm_inner, count=1), True
    new = fm_inner.rstrip() + f"\n{key}: {value}"
    return new, True


def process_one(path: Path, tier: str, dry_run: bool) -> dict:
    raw = path.read_text(encoding="utf-8")
    fm_inner, rest, fm_open = parse_frontmatter(raw)
    r1, rn = TIER_BUDGETS[tier]

    changes = []
    new_fm = fm_inner
    for k, v in (
        ("tier", tier),
        ("token_budget_round1_words", str(r1)),
        ("token_budget_round_n_words", str(rn)),
    ):
        new_fm, changed = upsert_field(new_fm, k, v)
        if changed:
            changes.append(f"{k}={v}")

    if not changes:
        return {"agent": path.stem, "tier": tier, "changes": [], "applied": False}

    new_content = fm_open + new_fm + rest
    if not dry_run:
        path.write_text(new_content, encoding="utf-8", newline="\n")
    return {"agent": path.stem, "tier": tier, "changes": changes, "applied": not dry_run}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = not args.apply

    if not dry_run:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        backup_dir = BACKUP_ROOT / f"agents_pre_tier_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in AGENTS_DIR.glob("*.md"):
            shutil.copy2(f, backup_dir / f.name)
        print(f"Backup: {backup_dir}")

    results = []
    missing = []
    for name, tier in TIER_MAP.items():
        path = AGENTS_DIR / f"{name}.md"
        if not path.exists():
            missing.append(name)
            continue
        results.append(process_one(path, tier, dry_run))

    on_disk = {p.stem for p in AGENTS_DIR.glob("*.md")}
    not_in_map = sorted(on_disk - set(TIER_MAP.keys()))

    mode = "DRY-RUN" if dry_run else "APPLIED"
    changed = [r for r in results if r["changes"]]
    print(f"\n[{mode}] {len(changed)} changed, {len(results)-len(changed)} no-op")
    by_tier: dict[str, list[str]] = {"A": [], "B": [], "C": [], "D": []}
    for r in results:
        by_tier[r["tier"]].append(r["agent"])
    for t in "ABCD":
        print(f"  Tier {t} ({len(by_tier[t])}): {by_tier[t]}")
    if missing:
        print(f"\nMISSING (in tier map, not on disk): {missing}")
    if not_in_map:
        print(f"NOT IN TIER MAP (on disk, no tier assigned): {not_in_map}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
