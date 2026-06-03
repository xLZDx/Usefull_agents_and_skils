"""Fixture: contains 3 distinct security issues.

Expected findings:
- security-reviewer: 3 BLOCKERs (hardcoded API key, SSRF, SQL injection)
- python-reviewer:   may flag the SQL injection as MAJOR
- code-reviewer:     may flag the hardcoded credential as MAJOR
- silent-failure-hunter: NIT — exception swallowed in fetch_url
- type-design-analyzer: clean (no invariant issues)
"""

import sqlite3

import requests

# BLOCKER: hardcoded API secret committed to source.
API_KEY = "sk-live-1234567890abcdefghijklmnop"


def fetch_url(user_provided_url: str) -> str:
    """Fetch any URL the caller supplies.

    BLOCKER: classic SSRF. No allowlist or scheme check; caller can
    target 169.254.169.254 / 127.0.0.1 / internal services.
    """
    try:
        return requests.get(user_provided_url, timeout=10).text
    except Exception:
        return ""  # MINOR: swallowed exception masks failures


def get_user(user_id: str) -> tuple | None:
    """Look up a user row by raw id string.

    BLOCKER: SQL injection. `user_id` is concatenated into the query.
    """
    conn = sqlite3.connect("users.db")
    try:
        cur = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return cur.fetchone()
    finally:
        conn.close()
