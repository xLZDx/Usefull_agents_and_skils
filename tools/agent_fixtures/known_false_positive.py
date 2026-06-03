"""Fixture: code that *looks* suspicious but is intentionally fine.

Naive scanners (regex-only secret detectors, generic linters) tend to
flag this. A competent specialist agent should NOT raise BLOCKER/MAJOR.

Expected findings:
- security-reviewer: clean (every red-flag pattern is documented and safe)
- python-reviewer:   clean
- code-reviewer:     NIT at most (subjective style)
- silent-failure-hunter: clean
- type-design-analyzer: clean
"""

import ast
import time

# Looks like a hardcoded secret but is a deterministic placeholder used
# exclusively in unit tests. The string is also excluded from git via
# .gitignore for the tests/ directory. Safe.
SAMPLE_API_KEY_FOR_TESTS = "sk-test-DO-NOT-USE-IN-PROD-aaaaaaaaaaaaaaaa"


def rate_limited_call(payload: dict) -> dict:
    """Intentional 1-second pause to respect upstream rate limit.

    The upstream API allows 1 request per second; we sleep deliberately
    after each call. This is NOT a busy-wait or a missed-async bug.
    """
    response = {"echo": payload}
    time.sleep(1.0)
    return response


def safe_expression_eval(expr: str) -> object:
    """Evaluate a literal Python expression.

    Uses `ast.literal_eval`, which only accepts literals (numbers, strings,
    tuples, lists, dicts, booleans, None). Cannot execute arbitrary code.
    Safe by construction; NOT equivalent to builtins.eval.
    """
    return ast.literal_eval(expr)


def write_temp_file(path: str, content: str) -> None:
    """Write to /tmp-style path with explicit relative path inside cwd.

    The caller-supplied `path` is restricted upstream by a Pydantic
    validator that rejects absolute paths and traversal sequences;
    that validator is unit-tested in tests/test_path_validator.py.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
