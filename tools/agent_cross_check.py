"""N (2026-05-29) Empiricism CI hook -- agent finding cross-checker.

Per the Empiricism over Poetry rule (~/.claude/CLAUDE.md + <PROJECT_ROOT>/
CLAUDE.md, 2026-05-27): every load-bearing agent finding must cite a
concrete ``file:line``, and the cited code must actually do what the
agent claims. Findings that fail this check are CONFABULATIONS -- the
review process must surface them rather than silently dropping them.

This tool reads a JSON list of findings (from stdin or ``--input``)
and emits a verdict per finding. Exit code is non-zero when any
confabulation is present AND ``--enforce`` is passed.

Finding schema
--------------
::

  [
    {
      "agent":    "code-architect",          # required
      "severity": "BLOCKER" | "MAJOR" | "MINOR" | "NIT",  # required
      "file":     "src/foo.py",              # required (relative to repo root)
      "line":     123,                        # required (1-based)
      "claim":    "this function fails open"  # required (1-line summary)
    },
    ...
  ]

Verdicts
--------
* ``VERIFIED``                 -- file exists, line in range
* ``CONFABULATION_FILE_MISSING``  -- agent cited a path that does not exist
* ``CONFABULATION_LINE_MISSING``  -- file too short for cited line
* ``UNVERIFIABLE_NO_CITATION`` -- missing file or line field
* ``WARN_NO_KEYWORD_OVERLAP``  -- file:line resolves but no claim keyword
                                  appears in a +/- 5-line context window
                                  (downgraded -- soft signal only)

Exit status
-----------
* 0   -- no confabulations OR enforce flag absent
* 1   -- enforce mode and at least one CONFABULATION_* present
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

VERDICT_VERIFIED = "VERIFIED"
VERDICT_FILE_MISSING = "CONFABULATION_FILE_MISSING"
VERDICT_LINE_MISSING = "CONFABULATION_LINE_MISSING"
VERDICT_NO_CITATION = "UNVERIFIABLE_NO_CITATION"
VERDICT_NO_OVERLAP = "WARN_NO_KEYWORD_OVERLAP"
# DD (2026-05-29): under --strict-keywords, WARN_NO_KEYWORD_OVERLAP is
# promoted to CONFABULATION_NO_KEYWORD_OVERLAP -- treated like the
# file/line-missing class for ``--enforce`` purposes. Lets the
# operator use the tool as a hard CI gate when the review process
# guarantees claims will reference identifiers in the cited code.
VERDICT_NO_OVERLAP_STRICT = "CONFABULATION_NO_KEYWORD_OVERLAP"

CONFABULATION_VERDICTS = frozenset({
    VERDICT_FILE_MISSING, VERDICT_LINE_MISSING,
    VERDICT_NO_OVERLAP_STRICT,
})


@dataclass(frozen=True)
class CrossCheckResult:
    agent: str
    severity: str
    file: str
    line: int | None
    claim: str
    verdict: str
    context: str = ""
    line_end: int | None = None     # V (2026-05-29): span end if cited as range
    # WWW (2026-05-29): step-by-step decision trace -- which check
    # accepted or rejected the finding. Populated only when the caller
    # passes ``trace=True`` to ``cross_check``.
    trace: tuple[str, ...] = ()


def _resolve_path(relpath: str) -> Path:
    p = Path(relpath)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def _extract_keywords(claim: str) -> list[str]:
    """Pull identifier-shaped tokens from the claim string. We use these
    as soft keyword-overlap heuristics for WARN_NO_KEYWORD_OVERLAP."""
    return [
        tok
        for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", claim or "")
        if tok.lower() not in _STOPWORDS
    ]


_STOPWORDS = frozenset({
    # Lowercase comparison; see _extract_keywords.
    "the", "and", "for", "this", "that", "with", "into", "from",
    "should", "would", "could", "fails", "fail", "open", "closed",
    "function", "method", "class", "missing", "not", "any", "all",
    "use", "uses", "used", "code", "line", "file",
    # HH (2026-05-29): expanded stopword set after review observed that
    # short generic tokens were inflating the VERIFIED rate by trivial
    # substring matches against import statements / docstrings. The new
    # entries are review-meta nouns + Python language artefacts that
    # nearly always show up in any file regardless of the finding.
    "imports", "import", "module", "raise", "return", "returns",
    "exception", "exceptions", "error", "errors", "true", "false",
    "none", "self", "args", "kwargs", "param", "params", "type",
    "types", "value", "values", "default", "instance", "object",
    "list", "dict", "set", "tuple", "string", "int", "bool", "float",
    "test", "tests", "passed", "added", "new", "old", "fix", "fixes",
    "wrap", "wraps", "swallow", "swallows", "silent", "silently",
})


def cross_check(
    finding: dict, *, strict_keywords: bool = False,
    trace: bool = False,
) -> CrossCheckResult:
    agent = str(finding.get("agent") or "?")
    sev = str(finding.get("severity") or "?")
    rel = finding.get("file")
    line = finding.get("line")
    line_end_raw = finding.get("line_end")
    line_end: int | None = (
        int(line_end_raw) if isinstance(line_end_raw, int) else None
    )
    claim = str(finding.get("claim") or "")

    trace_steps: list[str] = [] if trace else []  # always usable

    def _ret(verdict: str, *, context: str = "") -> CrossCheckResult:
        return CrossCheckResult(
            agent=agent, severity=sev, file=str(rel or ""),
            line=line if isinstance(line, int) else None,
            line_end=line_end,
            claim=claim, verdict=verdict, context=context,
            trace=tuple(trace_steps) if trace else (),
        )

    if not rel or not isinstance(line, int) or line < 1:
        if trace:
            missing = []
            if not rel:
                missing.append("file")
            if not isinstance(line, int):
                missing.append("line(type)")
            elif line < 1:
                missing.append("line(<1)")
            trace_steps.append(
                f"step 1: citation incomplete -- missing {missing} -> "
                f"{VERDICT_NO_CITATION}"
            )
        return _ret(VERDICT_NO_CITATION)
    if trace:
        trace_steps.append(
            f"step 1: citation = {rel}:{line}"
            + (f"-{line_end}" if line_end else "") + " (OK)"
        )

    path = _resolve_path(str(rel))
    if not path.exists() or not path.is_file():
        if trace:
            trace_steps.append(
                f"step 2: path not found under {PROJECT_ROOT} -> "
                f"{VERDICT_FILE_MISSING}"
            )
        return _ret(VERDICT_FILE_MISSING,
                     context=f"path not found under {PROJECT_ROOT}")
    if trace:
        trace_steps.append(f"step 2: file present ({path}) (OK)")

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        if trace:
            trace_steps.append(
                f"step 3: read failed -- {type(exc).__name__}: {exc} -> "
                f"{VERDICT_FILE_MISSING}"
            )
        return _ret(VERDICT_FILE_MISSING,
                     context=f"read failed: {type(exc).__name__}: {exc}")

    lines = text.splitlines()
    span_top = max(line, line_end) if line_end else line
    if trace:
        trace_steps.append(
            f"step 3: read OK ({len(lines)} lines); span_top={span_top}"
        )
    if span_top > len(lines):
        if trace:
            trace_steps.append(
                f"step 4: cited line {line}"
                + (f"-{line_end}" if line_end else "")
                + f" > file length {len(lines)} -> "
                + f"{VERDICT_LINE_MISSING}"
            )
        return _ret(
            VERDICT_LINE_MISSING,
            context=f"file has {len(lines)} lines, cited {line}"
                    + (f"-{line_end}" if line_end else ""),
        )

    lo = max(0, line - 6)
    hi = min(len(lines), (line_end or line) + 5)
    ctx = "\n".join(lines[lo:hi])
    if trace:
        trace_steps.append(
            f"step 4: context window lines {lo + 1}..{hi} extracted"
        )

    keywords = _extract_keywords(claim)
    if trace:
        trace_steps.append(
            f"step 5: extracted {len(keywords)} keywords from claim "
            f"(stopwords filtered): {keywords[:6]}"
            + ("..." if len(keywords) > 6 else "")
        )
    if keywords and not any(kw in ctx for kw in keywords):
        verdict = (
            VERDICT_NO_OVERLAP_STRICT if strict_keywords
            else VERDICT_NO_OVERLAP
        )
        if trace:
            trace_steps.append(
                f"step 6: NO keyword overlap with context -> {verdict}"
            )
        return _ret(verdict, context=ctx)
    if trace:
        if not keywords:
            trace_steps.append("step 6: no non-stopword keywords -> bypass overlap")
        else:
            matched = [kw for kw in keywords if kw in ctx]
            trace_steps.append(
                f"step 6: keyword overlap found ({matched[:3]}"
                + ("..." if len(matched) > 3 else "")
                + f") -> {VERDICT_VERIFIED}"
            )

    return _ret(VERDICT_VERIFIED, context=ctx)


def cross_check_all(
    findings: list[dict], *, strict_keywords: bool = False,
    trace: bool = False,
) -> list[CrossCheckResult]:
    return [
        cross_check(f, strict_keywords=strict_keywords, trace=trace)
        for f in findings
    ]


def aggregate_per_agent(
    results: "list[CrossCheckResult]",
) -> "dict[str, dict]":
    """NN (2026-05-29): per-agent stats over a batch of cross-check
    results.

    Each agent gets a dict of:
      total                -- number of findings attributed to the agent
      verified             -- count of VERIFIED verdicts
      confabulations       -- count of any CONFABULATION_* verdict
      no_keyword_overlap   -- count of WARN_NO_KEYWORD_OVERLAP
      no_citation          -- count of UNVERIFIABLE_NO_CITATION
      confab_rate          -- confabulations / total (0.0 if total==0)
      verified_rate        -- verified / total

    Operator workflow: after each multi-agent review, run the workflow
    wrapper with ``--format json``, feed the result into
    ``aggregate_per_agent``, watch which agents have high confab rates,
    and adjust the consensus loop accordingly (low-trust agents may
    need stronger briefs or removal from the roster).
    """
    out: dict[str, dict] = {}
    for r in results:
        agent = r.agent or "?"
        slot = out.setdefault(agent, {
            "total": 0, "verified": 0, "confabulations": 0,
            "no_keyword_overlap": 0, "no_citation": 0,
            "confab_rate": 0.0, "verified_rate": 0.0,
        })
        slot["total"] += 1
        if r.verdict == VERDICT_VERIFIED:
            slot["verified"] += 1
        if r.verdict in CONFABULATION_VERDICTS:
            slot["confabulations"] += 1
        if r.verdict == VERDICT_NO_OVERLAP:
            slot["no_keyword_overlap"] += 1
        if r.verdict == VERDICT_NO_CITATION:
            slot["no_citation"] += 1
    for slot in out.values():
        t = slot["total"]
        if t > 0:
            slot["confab_rate"] = round(slot["confabulations"] / t, 4)
            slot["verified_rate"] = round(slot["verified"] / t, 4)
    return out


def render_markdown(results: list[CrossCheckResult]) -> str:
    lines = [
        "| # | agent | sev | file:line | verdict | claim |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        # V (2026-05-29): if the finding carries a line range, render
        # ``file:line-line_end`` so the operator sees the span.
        if r.line:
            end = getattr(r, "line_end", None)
            loc = f"{r.file}:{r.line}-{end}" if end else f"{r.file}:{r.line}"
        else:
            loc = r.file
        claim_short = (r.claim[:60] + "...") if len(r.claim) > 60 else r.claim
        lines.append(
            f"| {i} | {r.agent} | {r.severity} | `{loc}` | "
            f"**{r.verdict}** | {claim_short} |"
        )
    return "\n".join(lines)


_MD_FINDING_RE = re.compile(
    r"""
    \[(?P<severity>BLOCKER|MAJOR|MINOR|NIT)\]
    \s+
    (?P<file>[^:\s]+(?:\.[A-Za-z0-9_]+|\s*\(plan\)|\.md))
    :
    (?P<line>\d+)
    (?:-(?P<line_end>\d+))?      # V (2026-05-29): optional line-range
    \s+(?:--|—|-)\s+
    (?P<claim>[^\n]+)
    """,
    re.VERBOSE,
)


def parse_markdown_findings(text: str, *, default_agent: str = "?") -> list[dict]:
    """Q (2026-05-29): parse the markdown findings block agents produce.

    Recognises lines of the operator-locked review format:

    ::

        [BLOCKER|MAJOR|MINOR|NIT] file:line -- claim text
        [BLOCKER|MAJOR|MINOR|NIT] file:line-line_end -- claim text   (V)

    Lines that don't match are ignored. Each match becomes a finding
    dict compatible with :func:`cross_check` -- agent is set to
    ``default_agent`` because the markdown shape does not carry it
    per-finding (the operator typically labels the whole block by
    agent name in a surrounding heading).

    V (2026-05-29): line ranges (e.g. ``file.md:215-219``) are now
    supported. The finding stores ``line`` as the start of the range
    and an extra ``line_end`` field so callers can render the span.
    Plan-file citations in the multi-agent review of G1 v2 used
    line ranges; without this support they were silently dropped.
    """
    out: list[dict] = []
    for m in _MD_FINDING_RE.finditer(text or ""):
        try:
            line = int(m.group("line"))
        except ValueError:
            continue
        finding: dict = {
            "agent":    default_agent,
            "severity": m.group("severity"),
            "file":     m.group("file").strip(),
            "line":     line,
            "claim":    m.group("claim").strip(),
        }
        end_raw = m.group("line_end")
        if end_raw is not None:
            try:
                finding["line_end"] = int(end_raw)
            except ValueError:
                pass
        out.append(finding)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input", "-i", type=str, default=None,
        help="path to input file (default: read stdin). Format auto-"
             "detected unless --input-format is set.",
    )
    ap.add_argument(
        "--input-format", choices=("json", "markdown", "auto"),
        default="auto",
        help="'json' (list of finding dicts), 'markdown' (parses "
             "[SEV] file:line -- claim lines), or 'auto' (default; "
             "tries JSON first then falls back to markdown).",
    )
    ap.add_argument(
        "--agent", type=str, default="?",
        help="default agent name used when ingesting markdown findings "
             "(JSON findings carry their own 'agent' field).",
    )
    ap.add_argument(
        "--enforce", action="store_true",
        help="exit 1 when any CONFABULATION_* verdict is present",
    )
    ap.add_argument(
        "--strict-keywords", action="store_true",
        help="DD (2026-05-29): promote WARN_NO_KEYWORD_OVERLAP to "
             "CONFABULATION_NO_KEYWORD_OVERLAP so --enforce also "
             "rejects findings whose claim identifiers do not appear "
             "in the cited code's +/- 5-line context window. Use when "
             "the review process guarantees claims reference real "
             "identifiers.",
    )
    ap.add_argument(
        "--per-agent-stats", action="store_true",
        help="NN (2026-05-29): also emit per-agent confabulation + "
             "verified-rate stats. JSON mode adds a 'per_agent' key; "
             "markdown mode appends a stats table. Useful for tracking "
             "which agents have high confab rates and need stronger "
             "briefs or removal from the roster.",
    )
    ap.add_argument(
        "--include-context", action="store_true",
        help="LLL (2026-05-29): retain the +/- 5-line code context "
             "window in the result output. By default the context is "
             "computed but discarded after the keyword-overlap check; "
             "with this flag, the operator sees the cited code "
             "alongside each verdict for fast eyeball review.",
    )
    ap.add_argument(
        "--explain", action="store_true",
        help="WWW (2026-05-29): emit a step-by-step decision trace per "
             "finding. JSON output gains a ``trace`` array; markdown "
             "output appends a 'Decision trace' block. Operator forensic "
             "surface -- understand WHY a given finding got its verdict.",
    )
    ap.add_argument(
        "--severity-filter", choices=("BLOCKER", "MAJOR", "MINOR", "NIT"),
        default=None,
        help="DDDD (2026-05-29): drop findings whose severity is BELOW "
             "the threshold before cross-checking. Order: BLOCKER > "
             "MAJOR > MINOR > NIT. Useful for triage on large review "
             "rounds where the operator only wants to focus on the "
             "load-bearing severities.",
    )
    ap.add_argument(
        "--format", choices=("markdown", "json"), default="markdown",
        help="output format",
    )
    args = ap.parse_args(argv)

    if args.input:
        raw = Path(args.input).read_text(encoding="utf-8")
    else:
        # On Windows the default stdin encoding is the OEM codepage
        # (cp1252 typically). Force UTF-8 so em-dashes / unicode in
        # piped agent output decode correctly.
        try:
            sys.stdin.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        raw = sys.stdin.read()

    findings: list[dict]
    if args.input_format == "markdown":
        findings = parse_markdown_findings(raw, default_agent=args.agent)
    elif args.input_format == "json":
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"ERROR: input is not valid JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(parsed, list):
            print("ERROR: top-level JSON must be a list of findings",
                  file=sys.stderr)
            return 2
        findings = parsed
    else:  # auto
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError("not a list")
            findings = parsed
        except (json.JSONDecodeError, ValueError):
            findings = parse_markdown_findings(raw, default_agent=args.agent)
        if not findings:
            print(
                "ERROR: no findings parsed from input (tried JSON list "
                "then markdown). Pass --input-format to disambiguate.",
                file=sys.stderr,
            )
            return 2

    # DDDD: severity filter (drop below threshold).
    if args.severity_filter:
        order = {"BLOCKER": 4, "MAJOR": 3, "MINOR": 2, "NIT": 1}
        floor = order[args.severity_filter]
        before = len(findings)
        findings = [
            f for f in findings
            if order.get(str(f.get("severity") or "").upper(), 0) >= floor
        ]
        if not findings:
            print(
                f"WARN: --severity-filter={args.severity_filter} "
                f"dropped all {before} findings (no remaining work).",
                file=sys.stderr,
            )

    results = cross_check_all(
        findings,
        strict_keywords=args.strict_keywords,
        trace=args.explain,
    )

    def _result_dict(r: CrossCheckResult) -> dict:
        d = dict(r.__dict__)
        if not args.include_context:
            d.pop("context", None)
        if not args.explain:
            d.pop("trace", None)
        else:
            d["trace"] = list(d.get("trace", ()))
        return d

    if args.format == "json":
        payload: dict | list
        if args.per_agent_stats:
            payload = {
                "results":   [_result_dict(r) for r in results],
                "per_agent": aggregate_per_agent(results),
            }
        else:
            payload = [_result_dict(r) for r in results]
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(results))
        if args.include_context:
            # Append a context block per finding so the operator can
            # review the cited code window without leaving the
            # workflow.
            print()
            print("## Context windows")
            for i, r in enumerate(results, 1):
                if not r.context:
                    continue
                print()
                print(f"### {i} -- {r.file}:{r.line}"
                      + (f"-{r.line_end}" if r.line_end else "")
                      + f" [{r.verdict}]")
                print("```")
                print(r.context)
                print("```")
        if args.explain:
            print()
            print("## Decision trace")
            for i, r in enumerate(results, 1):
                if not r.trace:
                    continue
                print()
                print(f"### {i} -- {r.file}:{r.line} [{r.verdict}]")
                for step in r.trace:
                    print(f"  * {step}")
        if args.per_agent_stats:
            stats = aggregate_per_agent(results)
            print()
            print("| agent | total | verified | confab | confab_rate |")
            print("|---|---|---|---|---|")
            for agent in sorted(stats):
                s = stats[agent]
                print(
                    f"| {agent} | {s['total']} | {s['verified']} | "
                    f"{s['confabulations']} | {s['confab_rate']} |"
                )

    n_confab = sum(1 for r in results if r.verdict in CONFABULATION_VERDICTS)
    if args.enforce and n_confab > 0:
        print(
            f"\nENFORCE: {n_confab} confabulation(s) detected -- exit 1",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
