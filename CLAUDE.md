# agents-skills-repo — project instructions

## Identity

Source repository for **Useful Agents & Skills**: a reusable, project-agnostic collection of Claude
Code sub-agent specifications (`agents/*.md`) and skills (`skills/<name>/`). Remote `origin` is
`https://github.com/xLZDx/Usefull_agents_and_skils.git`, default branch `main`.

The repository's own stated constraint: **no secrets, no PII, no binding to any specific project.**
That is the product promise, not a nicety — a spec that only makes sense inside one of this machine's
other repositories does not belong here.

Not to be confused with `D:\Repo\AIRA`, which is an unrelated product (a Jira/Confluence/TestRail
assistant that happens to also use a multi-agent architecture).

## The distribution gap — the thing most likely to cause a wrong conclusion

This repository holds the **source** of the agent and skill specs. Installation is a manual copy:
`agents/*.md` into `~/.claude/agents/`, and each `skills/<name>/` into `~/.claude/skills/`.

The installed copies are therefore **separate files that do not track this repository**. Editing a
spec here changes nothing about the agents available in a running session, and an agent behaving a
certain way in a session is not evidence about what this repository currently contains. When a
question is about live behavior, read the installed copy; when it is about the source, read here; and
never assume the two are in sync without comparing them.

## What is actually here, as opposed to what the README says

`git ls-files skills` is the honest inventory. As of 2026-08-17: **36 agents** and **8 tracked
skills** — `agent-consensus`, `implementation-planner`, `ml-engineer`, `polyglot-developer-assistant`,
`rosetta`, `skill-creator`, `software-architect`, `workspace-docgen`.

Two discrepancies worth knowing before you quote a number:

- **`README.md` lists six skills.** It predates `rosetta` and `workspace-docgen` and was never
  updated. The README is also the install instruction, so it is the file most likely to be read by
  someone acting on it — fix it when you next touch this repository rather than working around it.
- **Three empty directories sit in `skills/`**: `arbitrage-helper`, `fitness-app-helper`,
  `trading-bot-helper`. They contain nothing, they are **untracked** (git cannot store an empty
  directory), and their names are project-bound, which is exactly what this repository promises not
  to hold. They are local residue from `5910e34`, the commit that removed the project-bound
  material. A directory listing therefore over-reports this repository by three; a `git ls-files`
  does not.

## Content rules

- Everything is Markdown specs — there is no build, no test suite and no runtime in this repository.
  Do not report a change here as "verified" on the basis of anything other than reading the file.
- Agent frontmatter (`name`, `description`, `tier`, token budgets) is load-bearing: `description`
  drives routing, so changing it changes which agent gets selected.
- Skills with a `REFERENCE.md` lazy-load it on demand to keep per-invocation context cheap. Preserve
  that split rather than inlining reference material into `SKILL.md`.
- `ml-engineer` references generic mlfinlab / AFML methodology and contains
  `<your local reference clones>` placeholders. Those placeholders are intentional and must stay
  generic — do not resolve them to paths on this machine.

## History — eleven commits, two of which are apologies

The whole arc, in order, because the shape of it is the lesson:

| Date | Commit | What it was |
|---|---|---|
| 2026-05-12 | `3d4fbc2` | Initial commit: 36 agents + 7 skills |
| 2026-05-12 | `1585e9b` | **Sanitize**: replace personal paths with placeholders |
| 2026-05-13 | `95668e3` | Add `ml-engineer` (AFML / mlfinlab specialist) |
| 2026-05-23 | `f9563e5` | Token Optimization v1.1 — trim 38 agents + 9 skills, ~-65% per-spawn cost |
| 2026-06-03 | `63742af` | Sanitized reusable agents/skills/hook/rules + token-opt tooling |
| 2026-06-03 | `5910e34` | Keep only agents + skills — remove workflow tooling and the project-bound agent |
| 2026-07-02 | `68348e2` | Add `workspace-docgen` (cherry-picked from Rosetta) |
| 2026-07-28 | `9a1b90d` | Add the on-demand `/rosetta` workflow skill (Gate 1) |
| 2026-07-29 | `d4689c1` | Codify the `/rosetta` review phase (Gate 2c) |
| 2026-08-03 | `957d9f7` | Pin `ml-engineer` to model `sonnet` |
| 2026-08-03 | `9beaa1f` | **Sanitize**: remove a leaked user-home path in the `agent-consensus` REFERENCE |

**Leakage is this repository's characteristic defect.** Two of eleven commits exist only to remove
machine-specific paths that had already been pushed to a public remote — `1585e9b` the day after
the initial commit, and `9beaa1f` nearly three months later in a file (`REFERENCE.md`) that loads
lazily and is therefore read less often. The product promise is "no secrets, no PII, no binding to
any specific project", and the failure mode is never a secret; it is a path like
`C:\Users\<name>\...` or `D:\Repo\<project>\...` written into an example. Grep for absolute paths
before every commit here, including inside `REFERENCE.md` files.

**Scope has narrowed deliberately, twice.** `5910e34` removed workflow tooling and a project-bound
agent — that is where the three empty `skills/` directories came from. Anything that only makes
sense inside one of this machine's other repositories belongs in that repository, not here. When in
doubt, the test from `5910e34` applies: would this file mean anything on a machine that has none of
the operator's projects on it?

**Cost is a first-class concern.** `f9563e5` cut per-spawn cost by roughly 65% by trimming the
specs themselves, and `957d9f7` pinned `ml-engineer` to `sonnet` rather than leaving it on a
larger model. Frontmatter carries `tier` and `token_budget_round1_words` /
`token_budget_round_n_words` for the same reason. A verbose new agent spec is not free; it is paid
on every spawn, forever.

**The `/rosetta` skill has an external record.** `9a1b90d` and `d4689c1` are Gate 1 and Gate 2c of
the rollout documented in `D:\Repo\_rosetta_rollout\ROLLOUT_FINAL_REPORT.md`. That report is worth
reading before changing `skills/rosetta/`: a five-agent review explicitly **killed** the
marketplace-plugin and mode-gated-hook designs (un-gateable, clobbered by updates, authority-
inverting, ~10–12K tokens per session) in favour of the on-demand skill that shipped. The
always-on variants are not unexplored options; they are rejected ones.
