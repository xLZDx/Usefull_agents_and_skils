# Useful Agents and Skills for Claude Code

A collection of subagents and skills for [Claude Code](https://claude.com/claude-code).

## Contents

- **`agents/`** — 36 specialized subagents (code review, build resolution, planning, refactoring, security, etc.)
- **`skills/`** — 7 skills (project context loaders, planners, skill creator)

## Installation

Copy the folders into your global Claude config:

```powershell
# Windows
Copy-Item agents\* "$env:USERPROFILE\.claude\agents\" -Recurse
Copy-Item skills\* "$env:USERPROFILE\.claude\skills\" -Recurse
```

```bash
# macOS / Linux
cp -r agents/* ~/.claude/agents/
cp -r skills/* ~/.claude/skills/
```

Restart Claude Code and the new agents/skills will be available.

## Agents Overview

### Code Review & Quality
`code-reviewer`, `python-reviewer`, `cpp-reviewer`, `flutter-reviewer`, `fastapi-reviewer`, `database-reviewer`, `network-config-reviewer`, `security-reviewer`, `code-architect`, `code-explorer`, `pr-test-analyzer`, `comment-analyzer`, `type-design-analyzer`, `silent-failure-hunter`

### Build / Error Resolution
`build-error-resolver`, `cpp-build-resolver`, `dart-build-resolver`, `pytorch-build-resolver`

### Planning & Architecture
`architect`, `planner`

### Testing & Operations
`tdd-guide`, `e2e-runner`, `network-troubleshooter`, `loop-operator`, `harness-optimizer`, `training-inspector`

### Refactoring & Cleanup
`code-simplifier`, `refactor-cleaner`, `performance-optimizer`, `doc-updater`

### Specialized
`a11y-architect`, `seo-specialist`, `conversation-analyzer`

### Open-Source Pipeline
`opensource-forker`, `opensource-sanitizer`, `opensource-packager`

## Skills Overview

- `implementation-planner` — Step-by-step execution plans
- `polyglot-developer-assistant` — Multi-language dev assistant
- `software-architect` — Architecture and system design
- `skill-creator` — Create / edit / improve skills
- `trading-bot-helper`, `fitness-app-helper`, `arbitrage-helper` — Project-specific context loaders (may need path adjustments for your environment)

## License

MIT
