"""Phase 1.3 — append Output Budget block to top-N verbose agent bodies.

The block instructs the spawned agent to keep findings concise:
- Round 1 reviews: <=500 words total, structured by severity
- Round 2-3 classification: <=200 words, one sentence per item

Idempotent: skips agents that already contain '## Output budget'.

Run:
    python tools/agent_add_output_budget.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENTS_DIR = Path.home() / ".claude" / "agents"
BACKUP_ROOT = Path.home() / ".claude" / "agent_backups"

# Top-10 verbose agents by body size in the 2026-05-23 baseline.
TARGETS = [
    "flutter-reviewer",
    "performance-optimizer",
    "code-reviewer",
    "opensource-packager",
    "dart-build-resolver",
    "a11y-architect",
    "opensource-forker",
    "opensource-sanitizer",
    "pytorch-build-resolver",
    "training-inspector",
    "ml-engineer",
    "security-reviewer",
    "database-reviewer",
    "cpp-build-resolver",
]

BUDGET_BLOCK = """

## Output budget

- Round 1 reviews: <=500 words total, structured as `BLOCKER` / `MAJOR` / `MINOR` / `NIT` with one-sentence justification per finding. No preamble, no recap.
- Round 2-3 classification: <=200 words, one sentence per peer finding (`AGREE` / `DISAGREE` / `REFINE` + justification). No re-explanation of accepted reasoning.
- Cite file:line for every finding. No prose narratives, no full-file rewrites.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = not args.apply

    if not dry_run:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        backup_dir = BACKUP_ROOT / f"agents_pre_budget_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in AGENTS_DIR.glob("*.md"):
            shutil.copy2(f, backup_dir / f.name)
        print(f"Backup written to: {backup_dir}")

    changed: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for name in TARGETS:
        path = AGENTS_DIR / f"{name}.md"
        if not path.exists():
            missing.append(name)
            continue
        content = path.read_text(encoding="utf-8")
        if "## Output budget" in content:
            skipped.append(name)
            continue
        new_content = content.rstrip() + BUDGET_BLOCK
        if dry_run:
            changed.append(name)
        else:
            path.write_text(new_content, encoding="utf-8", newline="\n")
            changed.append(name)

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"\n[{mode}] {len(changed)} appended, {len(skipped)} already had budget, {len(missing)} missing")
    print(f"Changed:  {changed}")
    if skipped:
        print(f"Skipped:  {skipped}")
    if missing:
        print(f"Missing:  {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
