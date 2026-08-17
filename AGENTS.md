# AGENTS.md — Useful Agents & Skills

Tool-agnostic conventions for any coding agent operating in this checkout. `CLAUDE.md` is the
Claude Code entry point and carries identity, the real inventory and the project history; this file
is for everyone else, and for the parts that apply regardless of which agent is reading them.

This repository is unusual, and the difference governs everything below: **it contains no program.**
Every file is a Markdown specification that some other tool loads at runtime. There is nothing to
build, nothing to run and no test suite. The only verification available is reading the file.

## Build / test / run

None. Do not report a change here as "tested", "verified" or "passing" — there is nothing that
could have produced such a result. The honest formulation is what you read and what you compared it
against.

The nearest thing to a runtime check is comparing a spec against its installed copy (see below),
and that is a diff, not a test.

## The distribution gap — the single most common wrong conclusion

This repository holds the **source** of the agent and skill specs. Installation is a manual copy:

```text
agents/*.md          ->  ~/.claude/agents/
skills/<name>/       ->  ~/.claude/skills/<name>/
```

The installed copies are ordinary files that do not track this repository. Therefore:

- Editing a spec here changes **nothing** about the agents available in a running session.
- An agent behaving a certain way in a session is **not evidence** about what this repository
  contains.
- When the question is about live behavior, read the installed copy. When it is about the source,
  read here. Never assume the two agree without diffing them.
- `~/.claude` is on `C:`, which is Write-denied to the assistant on this machine. Installation and
  re-installation are operator steps. Say so plainly rather than reporting an install as done.

## What must never enter a file here

The remote is public. Two of eleven commits in this repository's history exist solely to remove
material that had already been pushed:

- `1585e9b` (2026-05-12) — personal paths replaced with placeholders, one day after the initial
  commit.
- `9beaa1f` (2026-08-03) — a leaked user-home path removed from `skills/agent-consensus/REFERENCE.md`,
  nearly three months later, in a lazily-loaded file that gets read less often.

So, before every commit:

- **Grep for absolute paths.** `C:\Users\`, `D:\Repo\`, `D:\test 2\`, `/home/`, `/Users/`. This is
  the actual failure mode — never a credential, always a path in an example.
- **Check `REFERENCE.md` files too.** They are the ones that slipped through.
- No secrets, no PII, no organisation names, no ticket IDs.
- **No binding to a specific project.** The test from `5910e34`, the commit that enforced this:
  would this file mean anything on a machine that has none of the operator's projects on it? If not,
  it belongs in that project's repository.
- `ml-engineer`'s `<your local reference clones>` placeholders are intentional. Leave them
  unresolved.

## Editing a spec

- **Frontmatter is load-bearing.** `name`, `description`, `model`, `tier`,
  `token_budget_round1_words`, `token_budget_round_n_words`. `description` is what drives routing —
  changing it changes which agent gets selected for a task, which is a behavioral change even
  though nothing else in the file moved. Treat a `description` edit as a functional edit.
- **Every word is paid on every spawn.** `f9563e5` cut per-spawn cost by roughly 65% by trimming
  the specs, and `957d9f7` pinned `ml-engineer` to `sonnet` rather than a larger model. Adding
  three paragraphs of nuance to an agent spec is a recurring cost, not a one-off. Prefer removing a
  sentence to adding one.
- **Preserve the `SKILL.md` / `REFERENCE.md` split.** `REFERENCE.md` lazy-loads on demand, which is
  what keeps per-invocation context cheap. Inlining reference material into `SKILL.md` silently
  makes every invocation more expensive.
- **`skills/rosetta/` has a design record outside this repository.**
  `D:\Repo\_rosetta_rollout\ROLLOUT_FINAL_REPORT.md` documents a five-agent review that **rejected**
  the marketplace-plugin and mode-gated-hook designs as un-gateable, update-clobbered,
  authority-inverting and costly (~10–12K tokens/session), in favour of the on-demand skill that
  shipped. Do not re-propose an always-on mechanism without reading why the last one was killed.

## Inventory hygiene

Use `git ls-files skills` rather than a directory listing. Three empty, untracked, project-bound
directories (`arbitrage-helper`, `fitness-app-helper`, `trading-bot-helper`) are local residue from
`5910e34` and will over-report the repository by three. `README.md` under-reports it by two: it
lists six skills and predates `rosetta` and `workspace-docgen`.

Current truth: 36 agents, 8 tracked skills.

## Git safety

- Remote `origin` is `github.com/xLZDx/Usefull_agents_and_skils`, default branch `main`. It is
  public — assume anything committed is permanently disclosed, which is why the sanitize rule above
  is phrased as "before commit", not "before push".
- A local commit never implies permission to push. Push is a separate, explicit authorization for a
  specific commit list; read `git log @{u}..HEAD --oneline` and compare before attempting one.
- Never amend or force-push. Two sanitize commits are in this history precisely because the wrong
  content was already public; rewriting it away would not have unpublished it.
