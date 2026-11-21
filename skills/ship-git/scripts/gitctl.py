#!/usr/bin/env python3
"""Deterministic Git standards: branch names, commit subjects, push approval."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TYPES = {
    "feat": "new user-visible capability",
    "fix": "bug correction",
    "perf": "performance improvement",
    "chore": "maintenance, core tooling, or dependencies",
    "docs": "documentation only",
    "refactor": "restructure without behaviour change",
    "test": "tests only",
    "build": "build system",
    "ci": "CI configuration",
    "style": "formatting only",
    "revert": "revert a previous change",
}
COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|perf|chore|docs|refactor|test|build|ci|style|revert)"
    r"(?:\((?P<scope>[a-z0-9._/-]+)\))?(?P<breaking>!)?: (?P<subject>.+)$"
)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PR_TITLE_RE = re.compile(
    r"^(?P<type>feat|fix|perf|chore|docs|refactor|test|build|ci|style|revert)"
    r"\((?P<base>[a-z0-9._/-]+)\)(?P<breaking>!)?: (?P<subject>.+)$"
)


def approval_path() -> Path:
    return Path(os.environ.get("SHIP_GIT_APPROVAL_PATH", Path.home() / ".agents" / "PUSH_APPROVAL.json")).expanduser()


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        die(f"command failed: {' '.join(cmd)}\n{result.stderr.strip() or result.stdout.strip()}")
    return result


def cmd_branch(args: argparse.Namespace) -> None:
    if args.type not in TYPES:
        die(f"unknown type {args.type!r}; allowed: {', '.join(TYPES)}")
    if not SLUG_RE.match(args.slug):
        die("slug must be lowercase kebab-case (letters, digits, hyphens), max 64 chars")
    base_label = args.base.split("/")[-1]
    name = f"{args.type}({base_label})/{args.slug}"
    run(["git", "check-ref-format", "--branch", name])

    local = run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{args.base}"], check=False)
    start = args.base if local.returncode == 0 else f"origin/{args.base}"
    if start != args.base:
        remote = run(["git", "show-ref", "--verify", "--quiet", f"refs/remotes/{start}"], check=False)
        if remote.returncode != 0:
            die(f"base branch not found locally or on origin: {args.base}")

    if args.dry_run:
        print(name)
        return
    run(["git", "switch", "-c", name, start])
    print(f"BRANCH {name} (from {start})")


def _subject_from_args(args: argparse.Namespace) -> str:
    if args.file:
        path = Path(args.file)
        if not path.is_file():
            die(f"commit message file not found: {path}")
        lines = [
            line.strip() for line in path.read_text(errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not lines:
            die("commit message file is empty")
        return lines[0]
    if args.message is None:
        die("provide --message or --file")
    return args.message.strip()


def cmd_commit_msg(args: argparse.Namespace) -> None:
    subject = _subject_from_args(args)
    match = COMMIT_RE.match(subject)
    if not match:
        die(
            f"invalid commit subject: {subject!r}\n"
            "expected: <type>[(scope)][!]: <subject> — e.g. feat: add vehicle CPT"
        )
    text = match.group("subject")
    if len(subject) > 72:
        die(f"commit subject too long ({len(subject)} > 72)")
    if text.endswith("."):
        die("commit subject must not end with a period")
    if not text[0].islower():
        die("commit subject should start with a lowercase imperative verb")
    print(f"COMMIT OK: {subject}")


def cmd_pr_title(args: argparse.Namespace) -> None:
    title = (args.title or "").strip()
    match = PR_TITLE_RE.match(title)
    if not match:
        die(
            f"invalid PR title: {title!r}\n"
            "expected: <type>(<base-branch>): <subject> — e.g. feat(master): add vehicle CPT"
        )
    subject = match.group("subject")
    if len(title) > 72:
        die(f"PR title too long ({len(title)} > 72)")
    if subject.endswith("."):
        die("PR title subject must not end with a period")
    if not subject[0].islower():
        die("PR title subject should start with a lowercase imperative verb")
    print(f"PR TITLE OK: {title}")


def approve_payload(args: argparse.Namespace) -> dict:
    expires = datetime.now(timezone.utc) + timedelta(minutes=args.minutes)
    return {
        "issue": args.issue,
        "approved_by": args.by,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "expires": expires.isoformat(timespec="seconds"),
    }


def cmd_approve(args: argparse.Namespace) -> None:
    path = approval_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = approve_payload(args)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"APPROVAL RECORDED for {args.issue} until {payload['expires']}")
    print("Only proceed because the user explicitly asked you to publish.")


def cmd_guard_push(args: argparse.Namespace) -> None:
    path = approval_path()
    if not path.is_file():
        die(
            "NO PUSH APPROVAL. Ask the user first. After explicit consent run:\n"
            f"  python {Path(__file__)} approve --issue <issue-id>"
        )
    try:
        payload = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        die(f"approval file is unreadable: {exc}")
    if payload.get("approved_by") != "user":
        die("approval was not recorded as user-granted")
    try:
        expires = datetime.fromisoformat(payload["expires"])
    except (KeyError, ValueError):
        die("approval file has no valid expiry")
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        die("push approval has expired; ask again")
    if args.issue and payload.get("issue") != args.issue:
        die(f"approval is for {payload.get('issue')!r}, not {args.issue!r}")
    print(f"APPROVED: push allowed for {payload.get('issue')} until {payload['expires']}")


COMMIT_MSG_HOOK = """#!/bin/sh
# Installed by ship-git. Validates conventional commit subjects.
exec python3 "$HOME/.agents/skills/ship-git/scripts/gitctl.py" commit-msg --file "$1"
"""
PRE_PUSH_HOOK = """#!/bin/sh
# Installed by ship-git. Refuses to publish without explicit approval.
exec python3 "$HOME/.agents/skills/ship-git/scripts/gitctl.py" guard-push
"""


def cmd_install_hooks(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    hooks = repo / ".git" / "hooks"
    if not hooks.is_dir():
        die(f"not a git repository (no {hooks})")
    for name, body in (("commit-msg", COMMIT_MSG_HOOK), ("pre-push", PRE_PUSH_HOOK)):
        target = hooks / name
        if target.exists() and not args.force:
            die(f"{target} already exists; use --force to back it up and replace")
        if target.exists():
            target.rename(target.with_suffix(".bak"))
        target.write_text(body)
        target.chmod(0o755)
        print(f"INSTALLED {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("branch")
    p.add_argument("type", choices=sorted(TYPES))
    p.add_argument("base")
    p.add_argument("slug")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_branch)

    p = sub.add_parser("commit-msg")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--message")
    group.add_argument("--file")
    p.set_defaults(func=cmd_commit_msg)

    p = sub.add_parser("pr-title")
    p.add_argument("--title", required=True)
    p.set_defaults(func=cmd_pr_title)

    p = sub.add_parser("approve")
    p.add_argument("--issue", required=True)
    p.add_argument("--by", default="user")
    p.add_argument("--minutes", type=int, default=30)
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("guard-push")
    p.add_argument("--issue")
    p.set_defaults(func=cmd_guard_push)

    p = sub.add_parser("install-hooks")
    p.add_argument("--repo", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_install_hooks)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
