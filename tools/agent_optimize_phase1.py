"""Phase 1 of Token Optimization Plan v1.1.

Applies two transforms to ~/.claude/agents/*.md:
  1. Tool whitelist tightening (drop Bash/Write/Edit from pure-review agents).
  2. Description compression to <=120 chars.

Creates a timestamped backup at ~/.claude/agent_backups/
before any in-place edit. Idempotent: re-running on already-optimized agents
is a no-op.

Run:
    python tools/agent_optimize_phase1.py --apply
    python tools/agent_optimize_phase1.py --dry-run    # default

Per-agent decisions are encoded in TRANSFORMS below; review the dry-run
diff before applying.
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

# Per-agent transforms. Each entry:
#   tools: full new tools array (will REPLACE existing)
#   description: new description (will REPLACE existing), MUST be <=120 chars
# Omit a key to leave that field unchanged.
TRANSFORMS: dict[str, dict] = {
    "a11y-architect": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "WCAG 2.2 / accessibility audit for web + native. Use when designing UI, design systems, or auditing inclusivity.",
    },
    "architect": {
        "description": "System design, scalability, technical decisions. Use when planning features, big refactors, or arch choices.",
    },
    "build-error-resolver": {
        "description": "Build/TS error fixes with minimal diffs. Use when build fails or types break. No architectural edits.",
    },
    "code-architect": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Feature architecture from existing patterns: blueprint with files, interfaces, data flow, build order.",
    },
    "code-explorer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Trace execution paths, map architecture layers, document dependencies in existing code.",
    },
    "code-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Code review for quality, security, maintainability. Use immediately after writing/modifying code. MUST run.",
    },
    "code-simplifier": {
        "description": "Simplify recently-modified code for clarity/consistency while preserving behavior.",
    },
    "comment-analyzer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Analyze code comments for accuracy, completeness, comment rot risk.",
    },
    "conversation-analyzer": {
        "description": "Analyze conversation transcripts to find behaviors worth blocking via hooks. Triggered by /hookify.",
    },
    "cpp-build-resolver": {
        "description": "C++ build + CMake + linker + template error fixes. Use when C++ builds fail. Minimal changes.",
    },
    "cpp-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "C++ reviewer: memory safety, modern C++ idioms, concurrency, perf. MUST run on C++ code changes.",
    },
    "crash-math-agent": {
        "description": "BCGame crash probability/stats: EV/Kelly/RoR, power-law fits, survival theory. Grounds claims in data.",
    },
    "dart-build-resolver": {
        "description": "Dart/Flutter build/analyze/pub-conflict fixes. Use when builds fail. Minimal surgical changes.",
    },
    "database-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "PostgreSQL: query opt, schema, security, perf, migrations. Use when writing SQL or troubleshooting DB perf.",
    },
    "doc-updater": {
        "description": "Codemap + docs sync. Runs /update-codemaps + /update-docs; updates README, docs/CODEMAPS/*, guides.",
    },
    "e2e-runner": {
        "description": "E2E tests via Vercel Agent Browser / Playwright. Manages journeys, quarantines flaky tests, uploads artifacts.",
    },
    "fastapi-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "FastAPI reviewer: async correctness, DI, Pydantic, security, OpenAPI quality, prod readiness.",
    },
    "flutter-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Flutter/Dart code review: widgets, state mgmt, idioms, perf, accessibility, clean architecture.",
    },
    "harness-optimizer": {
        "description": "Analyze + improve local Claude harness config for reliability, cost, throughput.",
    },
    "loop-operator": {
        "description": "Operate autonomous /loop runs; monitor progress; intervene when loops stall.",
    },
    "ml-engineer": {
        "description": "Financial ML (AFML/mlfinlab): Triple Barrier, Purged K-Fold, Frac Diff, meta-labeling, CUSUM, bar construction.",
    },
    "network-config-reviewer": {
        "description": "Router/switch config review: security, correctness, stale refs, risky commands, missing guardrails.",
    },
    "network-troubleshooter": {
        "description": "Network diagnostics (connectivity/routing/DNS/policy) with OSI-layer read-only workflow + RCA.",
    },
    "opensource-forker": {
        "description": "Fork project for open-source: strip secrets (20+ patterns), placeholderize internals, generate .env.example.",
    },
    "opensource-packager": {
        "description": "Generate open-source packaging: CLAUDE.md, setup.sh, README, LICENSE, CONTRIBUTING, GH issue templates.",
    },
    "opensource-sanitizer": {
        "description": "Verify fork sanitization pre-release: scan 20+ regex patterns for secrets/PII/internal refs. PASS/FAIL report.",
    },
    "performance-optimizer": {
        "description": "Perf optimization: bottlenecks, slow code, bundle size, runtime perf. Memory leaks, render loops, algos.",
    },
    "planner": {
        "description": "Planner for complex features + refactoring. Auto-activated for feature impl, arch changes, big refactors.",
    },
    "pr-test-analyzer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "PR test coverage review: behavioral coverage + real bug prevention.",
    },
    "python-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Python reviewer: PEP 8, idioms, type hints, security, perf. MUST run on Python code changes.",
    },
    "pytorch-build-resolver": {
        "description": "PyTorch runtime/CUDA/training fixes: tensor shapes, device errs, gradients, DataLoader, mixed precision.",
    },
    "refactor-cleaner": {
        "description": "Dead code + duplicate cleanup. Runs knip/depcheck/ts-prune; safely removes unused code.",
    },
    "security-reviewer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Security audit: OWASP Top 10, secrets, SSRF, injection, crypto, authn/authz. Use after touching user input/auth.",
    },
    "seo-specialist": {
        "description": "Technical SEO: audits, on-page opt, schema markup, Core Web Vitals, sitemap/robots, content mapping.",
    },
    "silent-failure-hunter": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Find silent failures, swallowed errors, bad fallbacks, missing error propagation.",
    },
    "tdd-guide": {
        "description": "TDD enforcement: tests-first methodology. Use when writing features, fixing bugs, refactoring. 80%+ coverage.",
    },
    "training-inspector": {
        "description": "Training pipeline inspector (project-specific): coverage, missing/stale models, failed jobs, watchdog state, log health.",
    },
    "type-design-analyzer": {
        "tools": ["Read", "Grep", "Glob"],
        "description": "Analyze type design: encapsulation, invariant expression, usefulness, enforcement.",
    },
}


def parse_frontmatter(content: str) -> tuple[str, str, str]:
    """Return (frontmatter_block, body, line_ending) splitting on first --- block."""
    m = re.match(r"^(---\r?\n.*?\r?\n---\r?\n)(.*)$", content, re.DOTALL)
    if not m:
        raise ValueError("no frontmatter found")
    return m.group(1), m.group(2), "\r\n" if "\r\n" in m.group(1) else "\n"


def update_frontmatter_field(fm: str, key: str, new_value: str) -> tuple[str, bool]:
    """Update a single key in a YAML-ish frontmatter block.

    Returns (updated_fm, changed). Idempotent.
    """
    pattern = re.compile(rf"^({re.escape(key)}\s*:\s*)(.*)$", re.MULTILINE)
    match = pattern.search(fm)
    if not match:
        return fm, False
    if match.group(2) == new_value:
        return fm, False
    updated = pattern.sub(lambda m: m.group(1) + new_value, fm, count=1)
    return updated, True


def format_tools_value(tools: list[str]) -> str:
    """Emit tools array in the canonical JSON-style form."""
    inner = ", ".join(f'"{t}"' for t in tools)
    return f"[{inner}]"


def transform_one(path: Path, transform: dict, dry_run: bool) -> dict:
    """Apply transform to a single agent file; return diff summary."""
    raw = path.read_text(encoding="utf-8")
    fm_block, body, _ = parse_frontmatter(raw)
    fm_inner = fm_block.strip().strip("-").strip()

    changes = []
    new_fm = fm_inner

    if "tools" in transform:
        new_tools_value = format_tools_value(transform["tools"])
        new_fm, changed = update_frontmatter_field(new_fm, "tools", new_tools_value)
        if changed:
            changes.append(f"tools -> {new_tools_value}")

    if "description" in transform:
        desc = transform["description"]
        if len(desc) > 120:
            raise ValueError(f"description for {path.stem} exceeds 120 chars: {len(desc)}")
        new_fm, changed = update_frontmatter_field(new_fm, "description", desc)
        if changed:
            changes.append(f"description -> ({len(desc)}c)")

    if not changes:
        return {"agent": path.stem, "changes": [], "applied": False}

    new_content = f"---\n{new_fm}\n---\n{body}"

    if not dry_run:
        path.write_text(new_content, encoding="utf-8", newline="\n")

    return {"agent": path.stem, "changes": changes, "applied": not dry_run}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes; default is dry-run.")
    args = parser.parse_args()
    dry_run = not args.apply

    if not AGENTS_DIR.exists():
        print(f"ERROR: {AGENTS_DIR} not found", file=sys.stderr)
        return 1

    if not dry_run:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        backup_dir = BACKUP_ROOT / f"agents_pre_phase1_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in AGENTS_DIR.glob("*.md"):
            shutil.copy2(f, backup_dir / f.name)
        print(f"Backup written to: {backup_dir}")

    results = []
    for name, transform in TRANSFORMS.items():
        path = AGENTS_DIR / f"{name}.md"
        if not path.exists():
            print(f"WARN: {name}.md not found, skipping", file=sys.stderr)
            continue
        result = transform_one(path, transform, dry_run=dry_run)
        results.append(result)

    changed = [r for r in results if r["changes"]]
    skipped = [r for r in results if not r["changes"]]

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"\n[{mode}] {len(changed)} agents changed, {len(skipped)} no-op")
    for r in changed:
        print(f"  {r['agent']}:")
        for c in r["changes"]:
            print(f"    {c}")
    if skipped:
        print(f"\nNo-op agents (already at target): {[r['agent'] for r in skipped]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
