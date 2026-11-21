---
name: ship-eval
description: "Run deterministic regression cases against the agent system after any skill, script or rulebook config change. Use on 'run skill evals', 'verify the skills', 'check the agent system', or before handoff for ship-* changes. Writes last-report.md; no skill change is READY with failing evals."
---

# Ship Eval

Skills are code. When they change, run tests. A small manifest guards the
gates the rest of the system depends on: git standards, loop gates, teach
digest, telemetry, fast lane.

## Case format — `~/.agents/evals/manifest.json`

```json
{
  "id": "git-branch-standard",
  "skill": "ship-git",
  "command": "python3 ~/.agents/skills/ship-git/scripts/gitctl.py branch feat master add-vehicle-cpt --dry-run",
  "cwd": "~/.agents/evals/fixtures/git-repo",
  "expect_exit": 0,
  "expect_out": "feat\\(master\\)/add-vehicle-cpt"
}
```

Fields: `command` (required), `id`, `skill`, `cwd`, `env`, `expect_exit`
(default 0), `expect_out` / `forbid_out` (regex on stdout+stderr), `timeout`.
Keep fixtures under `~/.agents/evals/fixtures/`.

## Run and fix

```bash
E=~/.agents/skills/ship-eval/scripts/evalctl.py
python $E run                 # writes ~/.agents/evals/last-report.md
python $E run --skill ship-git
python $E run --format json
python $E doctor              # all system checks in one command
```

A failure means a contract broke. Fix the skill, rerun affected cases, then
the full suite. Never edit an expectation just to turn a case green — only
when the user deliberately changed the standard, and say so at handoff.
Attach `last-report.md` as verification evidence in the pipeline.
