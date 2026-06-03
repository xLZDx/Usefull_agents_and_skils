"""Phase 4: migrate Tier C classifier agents to Haiku.

Tier C agents (per Phase 2.2 classification):
  - comment-analyzer
  - opensource-sanitizer
  - pr-test-analyzer
  - refactor-cleaner

These are classification-heavy (AGREE/DISAGREE/scan-and-tag) rather than
reasoning-heavy. Haiku is 3-5x cheaper. After migration, run regression
fixtures and revert any agent that misses an expected BLOCKER/MAJOR.

Idempotent. Creates backup before edit.
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

TIER_C_TARGETS = [
    "comment-analyzer",
    "opensource-sanitizer",
    "pr-test-analyzer",
    "refactor-cleaner",
]


def update_model(path: Path, new_model: str, dry_run: bool) -> dict:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\r?\n)(.*?)(\r?\n---\r?\n)(.*)$", raw, re.DOTALL)
    if not m:
        return {"agent": path.stem, "changed": False, "reason": "no frontmatter"}
    fm_open, fm_inner, fm_close, body = m.group(1), m.group(2), m.group(3), m.group(4)

    pattern = re.compile(r"^(model\s*:\s*)(.*)$", re.MULTILINE)
    existing = pattern.search(fm_inner)
    if existing:
        if existing.group(2).strip() == new_model:
            return {"agent": path.stem, "changed": False, "reason": "already on target"}
        new_fm = pattern.sub(lambda mm: mm.group(1) + new_model, fm_inner, count=1)
    else:
        new_fm = fm_inner.rstrip() + f"\nmodel: {new_model}"

    if dry_run:
        return {"agent": path.stem, "changed": True, "reason": f"would set model={new_model}"}
    path.write_text(fm_open + new_fm + fm_close + body, encoding="utf-8", newline="\n")
    return {"agent": path.stem, "changed": True, "reason": f"set model={new_model}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--revert", action="store_true", help="revert to sonnet")
    args = parser.parse_args()
    dry_run = not args.apply
    target_model = "sonnet" if args.revert else args.model

    if not dry_run:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        backup_dir = BACKUP_ROOT / f"agents_pre_phase4_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in AGENTS_DIR.glob("*.md"):
            shutil.copy2(f, backup_dir / f.name)
        print(f"Backup: {backup_dir}")

    results = []
    for name in TIER_C_TARGETS:
        path = AGENTS_DIR / f"{name}.md"
        if not path.exists():
            print(f"WARN: {name}.md missing")
            continue
        results.append(update_model(path, target_model, dry_run))

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"\n[{mode}] target model: {target_model}")
    for r in results:
        print(f"  {r['agent']}: {r['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
