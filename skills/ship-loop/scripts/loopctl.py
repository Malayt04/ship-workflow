#!/usr/bin/env python3
"""Deterministic state controller for the ship-loop skill.

The agent does the thinking and the editing; this script owns the loop state and
refuses to advance stages or declare readiness unless the evidence exists.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

STAGES = ["intake", "implement", "impact", "requirements", "review", "verify", "handoff"]
REQUIRED_ARTIFACT = {
    "intake": "spec.md",
    "impact": "impact.md",
    "requirements": "traceability.md",
    "review": "review.md",
    "verify": "verification.md",
    "handoff": "handoff.md",
}
GATES = ("review", "verify")
COMPACT_ARTIFACT = "fastlane.md"
COMPACT_SECTIONS = ("intake", "implement", "impact", "requirements", "review", "verify", "handoff")


def stage_artifact(state: dict, work_root: str, issue: str, stage: str) -> Path:
    """Return the artifact that proves a stage is complete."""
    base = Path(work_root) / issue
    if state.get("compact"):
        return base / COMPACT_ARTIFACT
    return base / REQUIRED_ARTIFACT[stage]


def check_artifact(path: Path, stage: str, compact: bool) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        die(f"stage {stage} requires a non-empty artifact: {path}")
    if compact:
        pattern = rf"^##\s+{re.escape(stage)}\b"
        if not re.search(pattern, path.read_text(), re.IGNORECASE | re.MULTILINE):
            die(f"{path} is missing the '## {stage}' section")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def state_path(issue: str, root: Path) -> Path:
    return root / issue / "loop-state.json"


def load(state_file: Path) -> dict:
    if not state_file.exists():
        die(f"no loop state at {state_file}; run 'init <issue>' first")
    return json.loads(state_file.read_text())


def save(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2) + "\n")


def record(state: dict, event: str, detail: str = "") -> None:
    state["history"].append({"at": now(), "event": event, "detail": detail})


def mark_timing(state: dict, stage: str) -> None:
    """Record when a stage finished; old states without timings stay readable."""
    state.setdefault("timings", {})[stage] = now()


def has_code_changes(cwd: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
    except OSError:
        return True  # not a git repo; do not block the loop
    if result.returncode != 0:
        return True
    lines = [line for line in result.stdout.splitlines() if ".agent-work/" not in line]
    return bool(lines)


def cmd_init(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    if path.exists() and not args.force:
        die(f"loop already initialised at {path}; use --force to reset")
    state = {
        "issue": args.issue,
        "created": now(),
        "max_iterations": args.max_iterations,
        "iteration": 1,
        "stage": "intake",
        "status": "RUNNING",
        "compact": bool(args.compact),
        "gates": {gate: {"passed": False, "detail": ""} for gate in GATES},
        "timings": {},
        "history": [],
    }
    record(state, "init", f"max_iterations={args.max_iterations} compact={args.compact}")
    save(path, state)
    print(f"INIT {args.issue}: stage=intake iteration=1/{args.max_iterations}")


def cmd_status(args: argparse.Namespace) -> None:
    state = load(state_path(args.issue, Path(args.work_root)))
    missing = []
    if state.get("compact"):
        compact_file = Path(args.work_root) / args.issue / COMPACT_ARTIFACT
        text = compact_file.read_text() if compact_file.is_file() else ""
        for section in COMPACT_SECTIONS:
            if not re.search(rf"^##\s+{section}\b", text, re.IGNORECASE | re.MULTILINE):
                missing.append(f"{COMPACT_ARTIFACT}#{section}")
    else:
        for stage, artifact in REQUIRED_ARTIFACT.items():
            if not (Path(args.work_root) / args.issue / artifact).is_file():
                missing.append(artifact)
    print(json.dumps({
        "issue": state["issue"],
        "status": state["status"],
        "stage": state["stage"],
        "iteration": f'{state["iteration"]}/{state["max_iterations"]}',
        "gates": {g: v["passed"] for g, v in state["gates"].items()},
        "missing_artifacts": missing,
        "history_tail": state["history"][-5:],
    }, indent=2))


def cmd_complete(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    state = load(path)
    if state["status"] != "RUNNING":
        die(f'loop status is {state["status"]}; run resume or escalate to the user')
    stage = args.stage
    if stage != state["stage"]:
        die(f'current stage is {state["stage"]}, not {stage}')
    artifact = REQUIRED_ARTIFACT.get(stage) if not state.get("compact") else COMPACT_ARTIFACT
    if artifact:
        target = Path(args.artifact) if args.artifact else stage_artifact(state, args.work_root, args.issue, stage)
        check_artifact(target, stage, bool(state.get("compact")))
    elif stage == "implement" and not has_code_changes(Path.cwd()):
        die("stage implement requires at least one code change in the worktree")
    mark_timing(state, stage)
    record(state, f"complete:{stage}", args.note or "")
    if stage == "handoff":
        failed = [g for g in GATES if not state["gates"][g]["passed"]]
        if failed:
            die(f"cannot mark handoff complete with failed gates: {', '.join(failed)}")
        state["status"] = "READY"
        print("READY: all stages complete and gates passed. Run 'handoff' to get the final message.")
    else:
        state["stage"] = STAGES[STAGES.index(stage) + 1]
        print(f'ADVANCE: {stage} complete → {state["stage"]}')
    save(path, state)


def cmd_gate(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    state = load(path)
    gate = args.gate
    if gate not in GATES:
        die(f"gate must be one of: {', '.join(GATES)}")
    if gate != state["stage"]:
        die(f'current stage is {state["stage"]}; gate {gate} belongs to that stage')

    if args.run:
        if not args.passed:
            die("--run requires --passed")
        if not args.evidence:
            die("--run requires --evidence <file>")
        proc = subprocess.run(
            shlex.split(args.run), capture_output=True, text=True, check=False
        )
        evidence_file = Path(args.evidence).expanduser()
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text(proc.stdout + proc.stderr)
        args.detail = (args.detail + " | " if args.detail else "") + f"run={args.run!r}"
        if proc.returncode != 0:
            args.passed = False
            args.detail += f" exit={proc.returncode}"

    state["gates"][gate] = {"passed": args.passed, "detail": args.detail or ""}
    mark_timing(state, gate)
    record(state, f"gate:{gate}={'pass' if args.passed else 'fail'}", args.detail or "")
    if not args.passed:
        _loop_back(state, f"{gate} gate failed: {args.detail or 'no detail'}")
        print(f'GATE FAIL: {gate} → back to implement, iteration {state["iteration"]}/{state["max_iterations"]}')
    else:
        evidence = _check_evidence(args)
        state["gates"][gate]["detail"] += f" | evidence={evidence}"
        state["stage"] = STAGES[STAGES.index(gate) + 1]
        print(f'GATE PASS: {gate} → {state["stage"]} (evidence: {evidence})')
    save(path, state)


def _check_evidence(args: argparse.Namespace) -> str:
    """A passing gate must point at evidence that actually says it passed."""
    if not args.evidence:
        die("--evidence <file> is required for --passed")
    evidence = Path(args.evidence)
    if not evidence.is_file() or evidence.stat().st_size == 0:
        die(f"evidence file missing or empty: {evidence}")
    text = evidence.read_text(errors="replace")
    if args.pass_pattern.lower() not in text.lower():
        die(f"evidence lacks pass pattern {args.pass_pattern!r}: {evidence}")
    if re.search(r"\b(failed|error|traceback)\b", text, re.IGNORECASE):
        die(f"evidence contains failure markers: {evidence}")
    return str(evidence)


def _loop_back(state: dict, reason: str) -> None:
    record(state, "loop-back", reason)
    if state["iteration"] >= state["max_iterations"]:
        state["status"] = "ESCALATED"
        record(state, "escalate", "iteration budget exhausted")
    else:
        state["iteration"] += 1
        state["stage"] = "implement"
        for gate in GATES:
            state["gates"][gate] = {"passed": False, "detail": ""}


def cmd_fail(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    state = load(path)
    _loop_back(state, args.reason)
    record(state, "fail", args.reason)
    print(
        f'FAIL recorded: {args.reason}\n'
        f'status={state["status"]} stage={state["stage"]} '
        f'iteration={state["iteration"]}/{state["max_iterations"]}'
    )
    save(path, state)


def cmd_checkpoint(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    state = load(path)
    state["status"] = "WAITING_HUMAN"
    record(state, "checkpoint", args.question)
    save(path, state)
    print(f"WAITING_HUMAN: {args.question}")


def cmd_resume(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    state = load(path)
    if state["status"] != "WAITING_HUMAN":
        die(f'status is {state["status"]}, not WAITING_HUMAN')
    state["status"] = "RUNNING"
    record(state, "resume", args.note or "")
    save(path, state)
    print("RESUMED")


def stage_duration_seconds(state: dict) -> dict[str, float]:
    timings = state.get("timings") or {}
    ordered = [s for s in STAGES if s in timings]
    result: dict[str, float] = {}
    for previous, current in zip(ordered, ordered[1:]):
        try:
            start = datetime.fromisoformat(timings[previous])
            end = datetime.fromisoformat(timings[current])
        except (TypeError, ValueError):
            continue
        result[current] = max(0.0, (end - start).total_seconds())
    return result


def cmd_telemetry(args: argparse.Namespace) -> None:
    roots = [Path(r).expanduser() for r in args.root]
    if not roots:
        roots = [Path.cwd() / ".agent-work", Path.home() / ".agents" / ".agent-work"]
    found: dict[Path, Path] = {}
    for root in roots:
        if root.is_dir():
            for path in root.rglob("loop-state.json"):
                found[path.resolve()] = path
    states = []
    for path in found.values():
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        data["_path"] = str(path)
        states.append(data)

    statuses = Counter(d.get("status", "UNKNOWN") for d in states)
    stages = Counter(d.get("stage", "unknown") for d in states)
    gates = Counter(
        f"{name}:{'pass' if value.get('passed') else 'fail'}"
        for d in states for name, value in d.get("gates", {}).items()
    )
    reasons = Counter(
        item.get("detail", "") for d in states for item in d.get("history", [])
        if item.get("event") in ("loop-back", "fail") and item.get("detail")
    )
    utilisation = [
        d.get("iteration", 1) / d.get("max_iterations", 6)
        for d in states if d.get("max_iterations")
    ]
    average = sum(utilisation) / len(utilisation) if utilisation else 0.0
    timing_samples: dict[str, list[float]] = {}
    for data in states:
        for stage, seconds in stage_duration_seconds(data).items():
            timing_samples.setdefault(stage, []).append(seconds)
    timing_avg = {
        stage: sum(values) / len(values) for stage, values in timing_samples.items()
    }
    timing_text = ", ".join(
        f"{stage}: {seconds:.0f}s" for stage, seconds in sorted(timing_avg.items())
    ) or "none"

    if args.format == "json":
        text = json.dumps({
            "generated": now(), "loops": len(states),
            "statuses": dict(statuses), "stages": dict(stages),
            "gates": dict(gates), "failure_reasons": dict(reasons.most_common(10)),
            "average_iteration_utilisation": round(average, 2),
            "average_stage_seconds": {k: round(v, 1) for k, v in timing_avg.items()},
            "details": [{k: d.get(k) for k in ("issue", "status", "stage", "iteration", "max_iterations")} for d in states],
        }, indent=2)
    else:
        lines = [
            f"# Loop telemetry — {now()[:10]}",
            "",
            f"- Loops found: **{len(states)}**",
            f"- By status: {', '.join(f'{k}: {v}' for k, v in sorted(statuses.items())) or 'none'}",
            f"- By stage: {', '.join(f'{k}: {v}' for k, v in sorted(stages.items())) or 'none'}",
            f"- Gates: {', '.join(f'{k}: {v}' for k, v in sorted(gates.items())) or 'none'}",
            f"- Loop-backs recorded: {sum(reasons.values())}",
            f"- Average iteration utilisation: {average:.0%}",
            f"- Stage timing: {timing_text}",
        ]
        if reasons:
            lines += ["", "## Top loop-back reasons", ""]
            lines += [f"- {reason} ({count}x)" for reason, count in reasons.most_common(10)]
        lines += ["", "## Loops", "", "| Issue | Status | Stage | Iteration |", "|---|---|---|---|"]
        for d in states:
            lines.append(
                f'| {d.get("issue", "?")} | {d.get("status", "?")} | '
                f'{d.get("stage", "?")} | {d.get("iteration", "?")}/{d.get("max_iterations", "?")} |'
            )
        text = "\n".join(lines)
    if args.out:
        target = Path(args.out).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n")
        print(f"WROTE {target}")
    else:
        print(text)


def cmd_handoff(args: argparse.Namespace) -> None:
    path = state_path(args.issue, Path(args.work_root))
    state = load(path)
    if state["status"] != "READY":
        die(f'status is {state["status"]}; only READY loops may hand off')
    artifact = stage_artifact(state, args.work_root, args.issue, "handoff")
    if not artifact.is_file():
        die(f"missing {artifact}")
    print(artifact.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", default=".agent-work", help="work artifact root (default: .agent-work)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("issue")
    p.add_argument("--max-iterations", type=int, default=6)
    p.add_argument("--compact", action="store_true", help="fast lane: one fastlane.md with ## <stage> sections")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    for name, func in (("status", cmd_status),):
        p = sub.add_parser(name)
        p.add_argument("issue")
        p.set_defaults(func=func)

    p = sub.add_parser("complete")
    p.add_argument("issue")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("--artifact")
    p.add_argument("--note")
    p.set_defaults(func=cmd_complete)

    p = sub.add_parser("gate")
    p.add_argument("issue")
    p.add_argument("gate")
    p.add_argument("--passed", dest="passed", action="store_true")
    p.add_argument("--failed", dest="passed", action="store_false")
    p.set_defaults(passed=True)
    p.add_argument("--detail")
    p.add_argument("--evidence", help="required with --passed: file containing pass output")
    p.add_argument("--run", help="execute this command and write its output to --evidence")
    p.add_argument("--pass-pattern", default="passed", help="marker expected in evidence (default: passed)")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("fail")
    p.add_argument("issue")
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_fail)

    p = sub.add_parser("checkpoint")
    p.add_argument("issue")
    p.add_argument("--question", required=True)
    p.set_defaults(func=cmd_checkpoint)

    p = sub.add_parser("resume")
    p.add_argument("issue")
    p.add_argument("--note")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("telemetry")
    p.add_argument("--root", action="append", default=[], help="folder containing <issue>/loop-state.json; repeatable")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--out", help="write report here")
    p.set_defaults(func=cmd_telemetry)

    p = sub.add_parser("handoff")
    p.add_argument("issue")
    p.set_defaults(func=cmd_handoff)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
