"""Phase 3.2 batch trim: remove common boilerplate from remaining top-10 agents.

Cuts applied per agent:
1. Remove "## Your Role" / "## Core Responsibilities" sections (header + body up to next ## header)
2. Compress generic intro paragraphs ("You are an expert X specialist...")
3. Strip "## Worked Example" / "## Example: ..." massive blocks (planner, opensource-*)
4. Strip embedded multi-block template chunks in opensource-packager (big README + CLAUDE.md
   embedded templates that bloat the agent body without changing competence — the agent can
   generate fresh ones from its instructions).

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

# Agents to trim in this batch (top-10 minus already-done top-3)
TARGETS = [
    "opensource-packager",
    "planner",
    "dart-build-resolver",
    "a11y-architect",
    "opensource-forker",
    "opensource-sanitizer",
    "architect",
]


def remove_section(body: str, header_re: str) -> tuple[str, bool]:
    """Remove `## Header ...` and everything until next `## ` header or EOF.

    Returns (new_body, changed).
    """
    pattern = re.compile(
        rf"^{header_re}.*?(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return body, False
    return pattern.sub("", body, count=1), True


def compress_intro(body: str) -> tuple[str, bool]:
    """Compress generic 'You are an expert X specialist...' opening paragraph.

    Matches the first paragraph after the title `# Header\n\n` if it starts with
    'You are' and ends at the next blank line. Replaces with empty string (agent name
    in frontmatter + first content section is enough).
    """
    pattern = re.compile(
        r"^(# [^\n]+\n\n)You are[^\n]+\.\s*(?=\n\n|\n##)",
        re.MULTILINE,
    )
    match = pattern.search(body)
    if not match:
        return body, False
    return pattern.sub(r"\1", body, count=1), True


def remove_planner_worked_example(body: str) -> tuple[str, bool]:
    """Planner-specific: remove '## Worked Example' through end-of-file-or-next-major-section."""
    pattern = re.compile(
        r"^## Worked Example.*?(?=^## (?:When Planning|Sizing|Red Flags|Output budget)|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return body, False
    return pattern.sub("", body, count=1), True


def remove_packager_embedded_templates(body: str) -> tuple[str, bool]:
    """opensource-packager-specific: remove the giant embedded README + CLAUDE.md template
    blocks under '### Step 2: Generate CLAUDE.md' through '### Step 7' Examples section.

    These templates bloat the agent without adding competence — the agent can generate
    fresh CLAUDE.md/README/etc. from its instructions and project context.

    We replace them with a brief instruction marker.
    """
    pattern = re.compile(
        r"(### Step 2: Generate CLAUDE\.md\n).*?(?=### Step 3:)",
        re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return body, False
    replacement = (
        "### Step 2: Generate CLAUDE.md\n\n"
        "Generate `CLAUDE.md` with: What (1-3 lines), Quick Start (3-5 commands), Commands (table), "
        "Architecture (component list), Key Files (table), Configuration (env vars), Contributing "
        "(brief). Match the project's actual stack; no boilerplate placeholders.\n\n"
    )
    return pattern.sub(replacement, body, count=1), True


def remove_packager_example_block(body: str) -> tuple[str, bool]:
    """Remove the long '## Examples' section in opensource-packager."""
    pattern = re.compile(
        r"^## Examples\b.*?(?=^## (?:Rules|Output budget)|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return body, False
    return pattern.sub("", body, count=1), True


def parse_frontmatter(content: str) -> tuple[str, str]:
    m = re.match(r"^(---\r?\n.*?\r?\n---\r?\n)(.*)$", content, re.DOTALL)
    if not m:
        raise ValueError("no frontmatter")
    return m.group(1), m.group(2)


def process_one(path: Path, dry_run: bool) -> dict:
    raw = path.read_text(encoding="utf-8")
    fm_block, body = parse_frontmatter(raw)
    orig_len = len(body)

    changes = []
    new_body = body

    for header in ("## Your Role\\b", "## Core Responsibilities\\b"):
        new_body, ch = remove_section(new_body, header)
        if ch:
            changes.append(f"removed {header.replace('\\b','')}")

    new_body, ch = compress_intro(new_body)
    if ch:
        changes.append("compressed 'You are X' intro")

    if path.stem == "planner":
        new_body, ch = remove_planner_worked_example(new_body)
        if ch:
            changes.append("removed Worked Example section")

    if path.stem == "opensource-packager":
        new_body, ch = remove_packager_embedded_templates(new_body)
        if ch:
            changes.append("collapsed embedded CLAUDE.md/README templates")
        new_body, ch = remove_packager_example_block(new_body)
        if ch:
            changes.append("removed Examples section")

    # Collapse triple+ blank lines to double
    new_body = re.sub(r"\n{3,}", "\n\n", new_body)

    new_len = len(new_body)
    delta_bytes = new_len - orig_len
    if changes and not dry_run:
        path.write_text(fm_block + new_body, encoding="utf-8", newline="\n")
    return {
        "agent": path.stem,
        "orig_bytes": orig_len,
        "new_bytes": new_len,
        "delta_bytes": delta_bytes,
        "delta_pct": (delta_bytes / orig_len * 100) if orig_len else 0,
        "changes": changes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = not args.apply

    if not dry_run:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        backup_dir = BACKUP_ROOT / f"agents_pre_phase3_2_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in AGENTS_DIR.glob("*.md"):
            shutil.copy2(f, backup_dir / f.name)
        print(f"Backup: {backup_dir}")

    results = []
    for name in TARGETS:
        path = AGENTS_DIR / f"{name}.md"
        if not path.exists():
            print(f"WARN: {name}.md missing")
            continue
        r = process_one(path, dry_run)
        results.append(r)

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"\n[{mode}] results:")
    print(f"{'agent':<28} {'orig':>6} {'new':>6} {'delta':>8} {'changes'}")
    for r in results:
        print(f"{r['agent']:<28} {r['orig_bytes']:>6} {r['new_bytes']:>6} {r['delta_pct']:+6.1f}%  {r['changes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
