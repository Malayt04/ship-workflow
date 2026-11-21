#!/usr/bin/env python3
"""Collect a day of agent work from git history and .agent-work artifacts."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ARTIFACTS = (
    "spec.md", "impact.md", "traceability.md", "review.md",
    "verification.md", "handoff.md", "rulebook-candidates.md",
)


def section(title: str, body: str) -> str:
    return f"### {title}\n```\n{body.rstrip() or '(none)'}\n```\n"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        return f"(git command unavailable: {' '.join(args)})"
    return result.stdout.strip()


def digest_repo(repo: Path, since: str, artifact_lines: int) -> str:
    out = [f"## Repository: {repo}"]
    out.append(section("Commits since " + since, git(
        repo, "log", f"--since={since} 00:00", "--date=short",
        "--pretty=format:%h | %ad | %an | %s",
    )))
    out.append(section("Uncommitted changes", git(repo, "status", "--short")))

    root = repo / ".agent-work"
    if not root.is_dir():
        out.append("_No .agent-work artifacts found._\n")
        return "\n".join(out)

    for issue_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        out.append(f"\n#### Issue: {issue_dir.name}")
        state = issue_dir / "loop-state.json"
        if state.is_file():
            try:
                data = json.loads(state.read_text())
                out.append(
                    f"- Loop: status={data.get('status')} stage={data.get('stage')} "
                    f"iteration={data.get('iteration')}/{data.get('max_iterations')}"
                )
            except ValueError:
                out.append("- Loop: state file unreadable")
        for name in ARTIFACTS:
            path = issue_dir / name
            if not path.is_file():
                continue
            lines = path.read_text(errors="replace").splitlines()
            excerpt = "\n".join(lines[:artifact_lines])
            if len(lines) > artifact_lines:
                excerpt += "\n…"
            out.append(section(name, excerpt))
    return "\n".join(out)


def collect_telemetry(repos: list[Path]) -> str:
    states = []
    for repo in repos:
        root = repo / ".agent-work"
        if root.is_dir():
            for path in root.rglob("loop-state.json"):
                try:
                    states.append(json.loads(path.read_text()))
                except ValueError:
                    continue
    statuses = Counter(d.get("status", "UNKNOWN") for d in states)
    reasons = Counter(
        item.get("detail", "") for d in states for item in d.get("history", [])
        if item.get("event") in ("loop-back", "fail") and item.get("detail")
    )
    lines = [
        "## Loop telemetry", "",
        f"- Loops found: {len(states)}",
        "- Status: " + (", ".join(f"{k}: {v}" for k, v in sorted(statuses.items())) or "none"),
        f"- Loop-backs: {sum(reasons.values())}",
    ]
    if reasons:
        lines.append("- Top reasons: " + "; ".join(f"{r} ({n}x)" for r, n in reasons.most_common(3)))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", required=True, help="YYYY-MM-DD")
    parser.add_argument("--repo", action="append", default=[], help="repeat for each repository")
    parser.add_argument("--artifact-lines", type=int, default=40)
    parser.add_argument("--out", help="write here instead of stdout")
    args = parser.parse_args()

    repos = [Path(r).expanduser().resolve() for r in args.repo] or [Path.cwd()]
    parts = [f"# Agent work digest — since {args.since}", "", collect_telemetry(repos), ""]
    for repo in repos:
        if not repo.is_dir():
            print(f"WARNING: not a directory: {repo}", file=sys.stderr)
            continue
        parts.append(digest_repo(repo, args.since, args.artifact_lines))
        parts.append("")
    text = "\n".join(parts)
    if args.out:
        target = Path(args.out).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        print(f"WROTE {target}")
    else:
        print(text)


if __name__ == "__main__":
    main()
