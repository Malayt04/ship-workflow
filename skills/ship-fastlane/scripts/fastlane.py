#!/usr/bin/env python3
"""Deterministic fast-lane gate and compact-artifact scaffolder."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RISKY = re.compile(
    r"(^|/)(migrations?|schema|auth|permission|security|secrets?|credentials?|"
    r"billing|payment|deploy|infra|core)(/|$)|"
    r"\.(sql|pem|key)$",
    re.IGNORECASE,
)


def die(message: str) -> None:
    print(f"INELIGIBLE: {message}", file=sys.stderr)
    raise SystemExit(2)


def git_files() -> list[str]:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.returncode != 0:
        die("not a git repository; pass --files explicitly")
    files = set()
    for line in result.stdout.splitlines():
        path = line[3:].split(" -> ")[-1]
        if ".agent-work/" not in path:
            files.add(path)
    return sorted(files)


def changed_lines(paths: list[str]) -> int:
    result = subprocess.run(["git", "diff", "--numstat", "--", *paths], capture_output=True, text=True)
    total = 0
    for line in result.stdout.splitlines():
        added, deleted, _ = (line.split("\t") + ["", "", ""])[:3]
        if added.isdigit():
            total += int(added)
        if deleted.isdigit():
            total += int(deleted)
    for path in paths:
        file = Path(path)
        if file.is_file() and subprocess.run(
            ["git", "ls-files", "--error-unmatch", path], capture_output=True
        ).returncode != 0:
            total += len(file.read_text(errors="replace").splitlines())
    return total


def cmd_check(args: argparse.Namespace) -> None:
    files = args.files or git_files()
    if not files:
        die("no changed files")
    if len(files) > 2:
        die(f"{len(files)} files changed; fast lane allows 2")
    for path in files:
        if RISKY.search(path):
            die(f"risky path: {path}")
    lines = changed_lines(files)
    if lines > 40:
        die(f"{lines} changed lines; fast lane allows 40")
    print(f"ELIGIBLE: {len(files)} file(s), {lines} changed lines")


def cmd_scaffold(args: argparse.Namespace) -> None:
    target = Path(args.work_root) / args.issue / "fastlane.md"
    if target.exists() and not args.force:
        print(f"EXISTS {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        ("intake", "Source, one-line change, one acceptance criterion."),
        ("implement", "What changed, and the fast-lane gate result."),
        ("impact", "Files checked; consumers of the changed symbol."),
        ("requirements", "AC → check mapping."),
        ("review", "Formatter/linter/test command and result."),
        ("verify", "Runtime proof command and evidence path."),
        ("handoff", "Status, evidence, NOT pushed."),
    ]
    body = [f"# Fast lane — {args.issue}", ""]
    for name, hint in sections:
        body += [f"## {name}", f"<!-- {hint} -->", ""]
    target.write_text("\n".join(body))
    print(f"WROTE {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", default=".agent-work")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("--files", nargs="*")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("scaffold")
    p.add_argument("issue")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scaffold)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
