# Commit Lifecycle

**Lifecycle:** `commit-before-phase -> build approved scope -> atomic local commit -> STOP + report -> separate push-GO -> push`.

1. **Commit BEFORE a new phase.** Create a clean rollback commit of the current state before starting any new implementation phase, especially multi-file refactors/migrations. Don't bundle unrelated fixes into a phase commit.

2. **Atomic / minimal commits.** Each commit is atomic, understandable, revertible, verified, scoped to ONE gate/sub-gate. GOOD: `Commit 0 - add tables` / `Commit 1 - add login`. BAD: one huge commit mixing auth + UI + integrations + refactor + tests.

3. **Todo list in every commit body.** End the commit body with a `## Todo list for this turn` section, each item with final status: `[x] completed` / `[ ] skipped (reason)` / `[~] deferred`. Makes `git log` a plan-vs-outcome audit.

4. **Commit local, then STOP. Push needs a separate push-GO.** After a phase is done & verified: `git add` + `git commit` (LOCAL) -> stop-and-report. **There is NO auto-push.** Run `git push` ONLY after a separate explicit push-GO (`push` / `push <gate-name>`).

5. **Never** force-push, never `--no-verify`, never bypass signing, never amend a pushed commit. If a hook fails, fix the issue and create a NEW commit.
