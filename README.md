# Useful Agents & Skills

A reusable, sanitized toolkit for [Claude Code](https://claude.com/claude-code): a roster of specialist sub-agents, generic skills, a token-cost-control hook, reusable workflow rules, and the tooling used to optimize agent prompts.

Everything here is **generic** — no secrets, no PII, no project-specific paths (project references were placeholderized to `<PROJECT_ROOT>`).

## Structure

```
agents/        37 specialist sub-agent specs (reviewers, resolvers, architects, ...)
skills/        6 generic skills:
               - agent-consensus       (multi-round peer-review loop)
               - ml-engineer           (AFML / quant ML review)
               - skill-creator         (author new skills)
               - implementation-planner
               - software-architect
               - polyglot-developer-assistant
hooks/         agent_spawn_gate.py     (PreToolUse hard-gate: blocks >3 heavy
                                         agent spawns in a burst without a tier-ack)
rules/         reusable workflow rules (paste into your CLAUDE.md):
               - gate-based-development.md
               - approval-gate.md
               - multi-agent-consensus.md
               - commit-lifecycle.md
tools/         token-optimization tooling + golden fixtures (audit, trim,
               tier-metadata, Haiku migration, regression fixtures)
settings.snippet.json   how to wire the hook into .claude/settings.json
```

## Install

- **Agents:** copy `agents/*.md` into `~/.claude/agents/`.
- **Skills:** copy each `skills/<name>/` into `~/.claude/skills/`.
- **Rules:** paste the contents of `rules/*.md` into your global `~/.claude/CLAUDE.md` (or a project `CLAUDE.md`). They are written to be project-agnostic.
- **Hook:** copy `hooks/agent_spawn_gate.py` into your project (e.g. `tools/hooks/`), then add the `settings.snippet.json` block to your project `.claude/settings.json` (replace `<PROJECT_ROOT>` and `<PY>`). Gitignore the runtime state dir `data/agent_review/`.

## The agent-spawn hard-gate (token control)

`hooks/agent_spawn_gate.py` is a `PreToolUse` hook on the `Agent` tool. It counts **heavy** spawns in a rolling 30s window and **denies the 4th+** unless a sentinel `data/agent_review/tier_ack.json` (written when you announce a confirmed T4 tier) is younger than 120s. "Light" (uncounted) = effective model is `haiku`. It is **fail-open** (any hook error -> the tool proceeds), stdlib-only, ASCII. This prevents accidental "spawn 6 heavy agents at once" token burns. See `rules/multi-agent-consensus.md` for the matching tiering policy.

## Token-optimization tooling (`tools/`)

Scripts that trim agent prompts + tool whitelists, add tier/budget metadata, and migrate classifier agents to Haiku — with a golden-fixture regression gate (`tools/agent_fixtures/`). Backups default to `~/.claude/agent_backups/`. Re-runnable (idempotent). These produced a ~-68% input-token reduction on a representative multi-agent review in the source project.

## License

Use freely.
