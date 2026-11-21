#!/usr/bin/env python3
"""One command for the final health check of the agent system."""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
SKILLS = HOME / ".agents/skills"
SCRIPTS = HOME / ".agents/scripts"
REPORT = HOME / ".agents/learning/doctor-latest.md"


def run(label: str, command: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(command, capture_output=True, text=True)
    output = (proc.stdout + proc.stderr).strip()
    ok = proc.returncode == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    return ok, output


def main() -> int:
    checks = []
    checks.append(("cross-root sync", run("cross-root sync", [sys.executable, str(SCRIPTS / "validate-skills.py")])))
    checks.append(("skill evals", run("skill evals", [sys.executable, str(SKILLS / "ship-eval/scripts/evalctl.py"), "run"])))

    stale = []
    wrong_path = []
    for path in (SKILLS.glob("ship-*/SKILL.md")):
        text = path.read_text()
        if re.search(r"feat\(master\)-", text):
            stale.append(path.parent.name)
        if "~/.config/opencode/skills" in text:
            wrong_path.append(path.parent.name)
    checks.append(("branch standard", (not stale, "stale branch form in: " + ", ".join(stale) if stale else "clean")))
    checks.append(("neutral skill paths", (not wrong_path, "harness-specific paths in: " + ", ".join(wrong_path) if wrong_path else "clean")))
    for name, ok in [("branch standard", not stale), ("neutral skill paths", not wrong_path)]:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")

    telemetry = HOME / ".agents/learning" / f"telemetry-{datetime.now(timezone.utc):%Y-%m-%d}.md"
    proc = subprocess.run([
        sys.executable, str(SKILLS / "ship-loop/scripts/loopctl.py"), "telemetry",
        "--root", str(Path.cwd() / ".agent-work"), "--out", str(telemetry),
    ], capture_output=True, text=True)
    print(f"[{'PASS' if proc.returncode == 0 else 'FAIL'}] telemetry")

    lines = ["# Doctor report", "", f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}", ""]
    for label, (ok, output) in checks:
        lines += [f"## {label}: {'PASS' if ok else 'FAIL'}", "```", output or "(no output)", "```", ""]
    lines += [f"- Telemetry: {telemetry}", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    failed = [label for label, (ok, _) in checks if not ok] + ([] if proc.returncode == 0 else ["telemetry"])
    print(f"REPORT {REPORT}")
    if failed:
        print("FAILED: " + ", ".join(failed), file=sys.stderr)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
