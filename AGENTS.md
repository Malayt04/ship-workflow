# Unified Agent Instructions

Global preferences, coding standards, and persona instructions shared across OpenCode, Claude Code, Codex, and Antigravity.

## Mandatory Ship Pipeline + Loop (all code-changing tasks, any stack)

Every task that modifies code, configuration, or product behaviour — in any
language (PHP/WordPress, Go, Rust, JS/TS, Python, infrastructure) — MUST invoke
`ship-pipeline` and run it as a closed loop via `ship-loop`. Stages: intake →
implement → impact → requirements → review → verification → handoff. Each stage
writes artifacts under `.agent-work/<issue-id>/` and records transitions with
`loopctl`. Only a loop with status READY may send the final handoff message; do
not send progress updates while it runs. The only early messages allowed are
checkpoints (design decisions, rulebook approvals) and escalations (budget
exhausted, blocked work).

Hard gates:
* Never push, open a PR, merge, or deploy without explicit user approval after handoff.
* Never mark a task complete without `review.md` and `verification.md` with passing critical checks.
* Every agent correction must become a deterministic check (lint/type/test) or an architectural fix; only judgment-based guidance becomes a prose rule.
* Propose rulebook additions with `ship-rulebook`; write to `~/.agents/AGENT_RULES.md` or `<repo>/docs/agent-rules.md` only after user approval.
* Keep skills task-agnostic: stack-specific commands belong in `references/stacks.md` adapters, never in generic stages.
* Use `ship-git` for every branch, commit and PR title: branches `<type>(<base>)/<slug>` (e.g. `feat(master)/add-vehicle-cpt`), commits `<type>: <name>`, PR titles `<type>(<base>): <name>` (e.g. `feat(master): add vehicle CPT`).
* Never push, open a PR, merge, or deploy even when broad local access is granted. Each publishing action needs fresh explicit approval and `ship-git guard-push` must pass.
* At the end of a workday, use `ship-teach` to turn the day's commits and `.agent-work` artifacts into a learning document for the user.
* Run `ship-eval` after any skill, script, or rulebook edit; a skill change is not READY with failing evals.

