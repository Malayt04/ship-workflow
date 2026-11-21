# agent-workflow

Version `0.2.0` — see [CHANGELOG.md](CHANGELOG.md).

Harness-neutral delivery system for agents. Use it to make any code change — fix,
feature, refactor or docs — pass the same gates before you review it.

## What it gives you
- Closed loop: intake → implement → impact → requirements → review → verify → handoff.
- Evidence gates: READY requires review.md and verification.md with saved output.
- One Git standard: branches `<type>(<base>)/<slug>`, commits `<type>: ...`, PR titles `<type>(<base>): ...`.
- Publishing approval: `ship-git guard-push` blocks pushes until you explicitly approve.
- Fast lane for ≤2 files / ≤40 changed lines; skills stay task-agnostic via stack adapters.

## Repository layout
- `skills/ship-*` — 12 skills: pipeline stages, loop, git, eval, fast lane, rulebook, teach.
- `scripts/` — `doctor.py` (health check), `validate-skills.py` (cross-root sync), `detect-stack.py`, `check-docs.py`.
- `evals/` — regression cases (`manifest.json`, fixtures).
- `AGENTS.md`, `AGENT_RULES.md` — agent instructions and rulebook R-001…R-013.

## Use it
Copy `skills/` into your harness skills path (e.g. `~/.agents/skills`, mirrored to
`~/.config/opencode/skills` and `~/.claude/skills`), then ask an agent to make a
change; `ship-pipeline` runs automatically.
```bash
python3 -I scripts/install.py          # copy skills/scripts/evals into harness roots
python3 -I scripts/install.py --check  # verify all roots match this repo
python3 -I scripts/doctor.py
python3 -I skills/ship-eval/scripts/evalctl.py run
python3 -I scripts/detect-stack.py --cwd /path/to/project
python3 -I scripts/check-docs.py --root .
```
Gates can capture their own evidence: `loopctl gate <issue> verify --passed --run "pytest -q" --evidence verification.md`.
`.github/workflows/validate.yml` runs install, doctor and evals on every push and PR.
READY means ready for your review — publishing still needs your explicit approval and a user-supplied token.
