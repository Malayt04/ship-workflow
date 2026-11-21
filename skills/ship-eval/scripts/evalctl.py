#!/usr/bin/env python3
"""Run deterministic regression cases against the agent skill system."""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MANIFEST = Path.home() / ".agents" / "evals" / "manifest.json"
DEFAULT_REPORT = Path.home() / ".agents" / "evals" / "last-report.md"


def expand(value: str) -> str:
    return os.path.expanduser(value.replace("$HOME", str(Path.home())))


def cmd_run(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest).expanduser()
    if not manifest.is_file():
        print(f"ERROR: manifest not found: {manifest}", file=sys.stderr)
        raise SystemExit(2)
    ensure_fixture_repo(manifest.parent / "fixtures" / "git-repo")
    cases = json.loads(manifest.read_text())
    if args.skill:
        cases = [case for case in cases if case.get("skill") == args.skill]
    if not cases:
        print("ERROR: no cases matched", file=sys.stderr)
        raise SystemExit(2)

    results = []
    for case in cases:
        env = os.environ.copy()
        for key, value in case.get("env", {}).items():
            env[key] = expand(str(value))
        cwd = Path(expand(case.get("cwd", str(Path.cwd()))))
        cwd.mkdir(parents=True, exist_ok=True)
        setup = case.get("setup")
        if setup:
            subprocess.run([expand(tok) for tok in shlex.split(setup)], cwd=cwd, env=env,
                           capture_output=True, text=True, check=False)
        try:
            proc = subprocess.run(
                [expand(tok) for tok in shlex.split(case["command"])], cwd=cwd, env=env,
                capture_output=True, text=True, timeout=case.get("timeout", 30),
            )
            code, combined = proc.returncode, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            code, combined = -1, "TIMEOUT"
        expected = case.get("expect_exit", 0)
        ok = code == expected
        if ok and case.get("expect_out"):
            ok = bool(re.search(case["expect_out"], combined, re.IGNORECASE))
        if ok and case.get("forbid_out"):
            ok = not re.search(case["forbid_out"], combined, re.IGNORECASE)
        results.append({
            "id": case.get("id", case["command"]),
            "skill": case.get("skill", "-"),
            "ok": ok,
            "exit": code,
            "expected_exit": expected,
            "output": combined.strip()[-600:],
        })

    passed = sum(1 for r in results if r["ok"])
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.format == "json":
        text = json.dumps({"generated": stamp, "passed": passed, "total": len(results), "results": results}, indent=2)
    else:
        lines = [
            "# Skill eval report", "",
            f"Generated: {stamp}",
            f"Result: **{passed}/{len(results)} passed**", "",
            "| Case | Skill | Result | Exit |", "|---|---|---|---|",
        ]
        for r in results:
            lines.append(f'| {r["id"]} | {r["skill"]} | {"PASS" if r["ok"] else "FAIL"} | {r["exit"]} (want {r["expected_exit"]}) |')
        failures = [r for r in results if not r["ok"]]
        if failures:
            lines += ["", "## Failures", ""]
            for r in failures:
                lines += [f"### {r['id']}", "```", r["output"] or "(no output)", "```", ""]
        text = "\n".join(lines)
    report = Path(args.report).expanduser()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(text + "\n")
    print(text if args.to_stdout else f"WROTE {report} — {passed}/{len(results)} passed")
    if passed != len(results):
        raise SystemExit(1)


def cmd_doctor(args: argparse.Namespace) -> None:
    doctor = Path.home() / ".agents" / "scripts" / "doctor.py"
    raise SystemExit(subprocess.run([sys.executable, str(doctor)]).returncode)


def ensure_fixture_repo(repo: Path) -> None:
    """The fixture repo's .git is not tracked; recreate it on a fresh clone."""
    if (repo / ".git").exists():
        return
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").touch()
    env = {**os.environ, "GIT_AUTHOR_NAME": "evals", "GIT_AUTHOR_EMAIL": "evals@localhost",
           "GIT_COMMITTER_NAME": "evals", "GIT_COMMITTER_EMAIL": "evals@localhost"}
    for cmd in (["git", "init", "-q", "-b", "master"], ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "chore: seed eval fixture"]):
        subprocess.run(cmd, cwd=repo, env=env, check=True, capture_output=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--report", default=str(DEFAULT_REPORT))
    p.add_argument("--skill")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--to-stdout", action="store_true")
    p.set_defaults(func=cmd_run)

    sub.add_parser("doctor", help="run every system health check").set_defaults(func=cmd_doctor)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
