# Expected Findings — Agent Regression Fixtures (Phase 0 baseline)

These five fixtures are the regression suite for the Token Optimization
Plan v1.1. After any phase that trims agent prompts (Phase 1 descriptions,
Phase 2 dedupe, Phase 3 body trim, Phase 4 Haiku migration), each Tier B
candidate agent is re-run on the relevant fixtures. The agent passes the
gate only if it produces **the same expected findings** (within +/-1).

## Tier B candidate agents

| Agent | Fixtures it must clear |
|---|---|
| code-reviewer | known_bug, known_security_issue, known_false_positive, clean_file, large_noisy |
| python-reviewer | known_bug, known_security_issue, known_false_positive, clean_file, large_noisy |
| security-reviewer | known_security_issue, known_false_positive, clean_file, large_noisy |
| silent-failure-hunter | known_security_issue, large_noisy, clean_file |
| type-design-analyzer | clean_file, large_noisy, known_bug |
| refactor-cleaner | clean_file, large_noisy |
| comment-analyzer | clean_file, large_noisy, known_false_positive |
| pr-test-analyzer | (uses real PR — separate fixture later) |

## Findings table

### `known_bug.py` — rolling-window off-by-one

| Agent | Expected severity | Expected message gist |
|---|---|---|
| code-reviewer | MAJOR | off-by-one window slice in `rolling_max` |
| python-reviewer | MAJOR | window of `window+1` instead of `window` |
| security-reviewer | clean | no security surface |
| silent-failure-hunter | clean | no swallowed errors |
| type-design-analyzer | NIT or clean | could add NewType for windowed series |

### `known_security_issue.py` — SSRF + SQLi + hardcoded secret

| Agent | Expected severity | Expected message gist |
|---|---|---|
| security-reviewer | 3 × BLOCKER | hardcoded `API_KEY`; SSRF in `fetch_url`; SQLi in `get_user` |
| python-reviewer | MAJOR | SQL injection via f-string |
| code-reviewer | MAJOR | hardcoded credential |
| silent-failure-hunter | NIT | bare `except Exception` in `fetch_url` |
| type-design-analyzer | clean | no type-design surface |

### `known_false_positive.py` — looks suspicious, is fine

| Agent | Expected severity | Expected message gist |
|---|---|---|
| security-reviewer | clean | every red-flag pattern is documented and safe |
| python-reviewer | clean | — |
| code-reviewer | NIT at most | subjective style only |
| silent-failure-hunter | clean | — |
| type-design-analyzer | clean | — |

Failure mode to watch for: a too-aggressive trim could make agents
hallucinate findings here. False-positive rate is the canary.

### `clean_file.py` — well-written code, no real issues

| Agent | Expected severity | Expected message gist |
|---|---|---|
| ALL Tier B | clean (NIT only) | no BLOCKER / MAJOR; possibly add docstring tests |

Failure mode: any agent that flags BLOCKER/MAJOR on this fixture is
hallucinating after the trim — revert that phase.

### `large_noisy.py` — 180 lines, ONE buried BLOCKER

| Agent | Expected severity | Expected message gist |
|---|---|---|
| silent-failure-hunter | BLOCKER | fail-open in `validate_order` (bare except returns True) |
| security-reviewer | MAJOR | risk gate fails open — bypass possible |
| python-reviewer | MAJOR | bare `except Exception` then `return True` |
| code-reviewer | MAJOR | exception swallow path returns wrong sentinel |
| type-design-analyzer | NIT | `Order` lacks `__post_init__` validation |
| refactor-cleaner | NIT or clean | nothing dead, no duplicates |

Failure mode for trim: if a trimmed agent **misses** the fail-open in
`validate_order`, that trim is over-aggressive — revert.

## How to run the regression after a phase trim

```powershell
# For each Tier B candidate agent and each relevant fixture:
# 1. Spawn the agent via Agent tool with prompt:
#    "Review tools/agent_fixtures/<fixture>.py for BLOCKER/MAJOR/MINOR/NIT findings."
# 2. Capture the response.
# 3. Compare against the expected severities + message gists in this file.
# 4. Pass iff: no missed BLOCKER, no missed MAJOR, +/-1 NIT tolerated.

# Pseudo-automation (one shell per phase):
# python tools/run_regression.py --phase 1 --agents tier_b
# (write that runner when entering Phase 2 — for now, manual A/B is fine)
```

## Update protocol

- When adding a new Tier B agent: add a row to the agent table and define
  the expected severity on each fixture.
- When changing a fixture: bump the file's docstring and re-baseline
  expected findings before the next regression run.
- Do NOT silently weaken expectations to make a failing trim "pass" —
  revert the trim instead.
