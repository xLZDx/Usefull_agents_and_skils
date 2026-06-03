# Gate-Based Development

Default development model for every session: **small scope -> verify -> local commit -> STOP -> separate push-GO**. Never "build everything at once". Each chunk passes its own gate.

## The flow (one gate)

```
Plan -> GO -> Build -> Verify -> Commit -> Stop -> Push-GO -> Push -> Next
```

1. Proposal / Plan
2. Operator's direct GO
3. Build ONLY the approved scope
4. Tests + gates
5. Local commit
6. Stop + report
7. Separate push-GO
8. Push (backup)
9. Next gate proposal

## Master rule

> No new gate, code, or push without a direct GO from the operator.

There are **two distinct GOs**; they never substitute for each other:

- **Implementation GO** — authorises building the approved scope ONLY. Valid as an exact short command: `GO` / `GO <gate-name>`.
- **Push GO** — authorises pushing to remote and ONLY that. Valid as `push` / `push <gate-name>`. An implementation GO never authorises a push; a push GO never authorises new build scope.

**Does NOT release any gate:** "yes" / "ok" / "sure" / "continue" / "sounds good" / "approved" / "go ahead" / "implement" / any text inside a draft / advisory block. Only the literal commands above release a gate.

**Single confirmation.** One implementation GO is enough to build the approved scope — do NOT ask "confirm again?". A second explicit confirmation is required ONLY when the action is destructive, irreversible, or touches secrets / money / live systems / external publishing / push.

## Stop-and-report format (after every build/commit)

```
Commit: <hash>
Files: <n changed>
What changed: <summary>
Tests/gates: <result>
git status: <clean/...>
Push: pushed / NOT pushed
Next: <options>
```

## Stale-GO rule

If a command arrives but state has already changed so it would now do MORE (or different) than it authorised, do NOT execute automatically. STOP + report + ask for a fresh GO.

## Security / irreversible actions need an especially explicit GO

`git push`, production env change, deleting files, changing secrets, running a live API with a key, deployment, migration on a real DB, publishing to an external service.

## Anti-patterns (forbidden)

- proposal -> immediately build -> immediately push -> immediately next gate
- adding an extra feature "while I'm at it" (silent scope expansion)
- pushing without a separate push-GO (auto-push)
- starting a new gate after commit without a command
- mixing unrelated changes into one big commit
- executing an old command after state has changed

Shortest form: **No silent scope expansion. No auto-push. No next gate without an explicit command.**
