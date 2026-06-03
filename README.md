# Useful Agents & Skills

A reusable, project-agnostic collection of [Claude Code](https://claude.com/claude-code) sub-agents and skills. No secrets, no PII, no binding to any specific project.

## Structure

```
agents/   specialist sub-agent specs (reviewers, resolvers, architects, planners, ...)
skills/   skills:
          - agent-consensus            (multi-round multi-agent peer-review loop)
          - ml-engineer                (AFML / quant ML review)
          - skill-creator              (author new skills)
          - implementation-planner
          - software-architect
          - polyglot-developer-assistant
```

## Install

- **Agents:** copy `agents/*.md` into `~/.claude/agents/`.
- **Skills:** copy each `skills/<name>/` into `~/.claude/skills/`.

Claude Code picks them up automatically. Each agent's frontmatter (`name`, `description`, `tier`, token budgets) is preserved; skills with a `REFERENCE.md` lazy-load it on demand to keep per-invocation context cheap.

## Notes

- These are generic specialist prompts — adapt the `description` fields to your own routing needs.
- `ml-engineer` references generic mlfinlab / AFML methodology; point its `<your local reference clones>` placeholders at your own copies if you use them.

## License

Use freely.
