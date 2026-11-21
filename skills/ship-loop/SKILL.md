---
name: ship-loop
description: "Run agentic work as a closed feedback loop: act → artifact → deterministic gate → advance or loop back. Use with ship-pipeline, on 'run in a loop' or 'don't message until done'. loopctl owns state; READY is the only handoff condition."
---

# Ship Loop

Failure is normal and cheap. The agent observes state, does work, writes an
artifact, and lets a deterministic evaluator decide: pass → next stage, fail →
record reason, return to implementation.

Four properties make this trustworthy:

1. `loop-state.json` on disk, not agent memory — any agent can resume.
2. Deterministic gates: artifacts must exist, be non-empty, and have pass
   evidence. The controller refuses to fake READY.
3. Bounded budget (`max_iterations`); exhaustion escalates to the user.
4. Checkpoints only for design decisions, rulebook approval, or escalation.

Termination: `status == READY`. Until then, keep working and stay quiet.

## Commands — from the worktree

```bash
L=~/.agents/skills/ship-loop/scripts/loopctl.py
python $L init <issue> --max-iterations 6
python $L status <issue>
python $L complete <issue> intake      --artifact .agent-work/<issue>/spec.md
python $L complete <issue> implement
python $L complete <issue> impact      --artifact .agent-work/<issue>/impact.md
python $L complete <issue> requirements --artifact .agent-work/<issue>/traceability.md
python $L gate <issue> review --passed --evidence .agent-work/<issue>/evidence/review.txt
python $L gate <issue> verify --passed --evidence .agent-work/<issue>/evidence/smoke.txt
python $L complete <issue> handoff --artifact .agent-work/<issue>/handoff.md
python $L handoff <issue>              # prints only when READY
```

Failure and pause:

```bash
python $L fail <issue> --reason "P1: unescaped output in renderer.php:42"
python $L checkpoint <issue> --question "Public endpoint or auth-only?"
python $L resume <issue>
```

`--passed` requires an evidence file with a pass marker (default `passed`) and
no failure markers. `--compact` uses one `fastlane.md` with `## <stage>` headings
instead of separate artifacts (see `ship-fastlane`).

## Rules

- Lock design decisions in `ship-intake` before starting. After that, checkpoint
  only on a genuinely new decision.
- Fix the code on a failed gate, not the artifact; rerun impact → requirements →
  review → verify.
- `WAITING_HUMAN` and `ESCALATED` are the only early messages allowed.
- READY means ready for *review*, never ready to publish. Keep the no-push rule.

## Budgets

| Task | Max iterations |
|---|---|
| Small fix / config / fast lane | 3 (fast lane: 2) |
| Feature / refactor | 6 |
| Cross-cutting | 10 |

Repeated failure at one gate means escalate and add a rulebook entry, not raise
the budget silently.

## Telemetry

```bash
python $L telemetry --root /path/to/repo/.agent-work --out ~/.agents/learning/telemetry-$(date +%F).md
```

Reports loops by status/stage, gate results, loop-back reasons, and iteration
utilisation. Feed it to `ship-teach`. Use `--format json` for scripting.
