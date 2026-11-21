# agent-workflow

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
- `scripts/` — `doctor.py` (health check), `validate-skills.py` (cross-root sync).
- `evals/` — 15 regression cases (`manifest.json`, fixtures).
- `AGENTS.md`, `AGENT_RULES.md` — agent instructions and rulebook R-001…R-012.

## Use it
Copy `skills/` into your harness skills path (e.g. `~/.agents/skills`, mirrored to
`~/.config/opencode/skills` and `~/.claude/skills`), then ask an agent to make a
change; `ship-pipeline` runs automatically.
```bash
python3 -I scripts/install.py          # copy skills/scripts/evals into harness roots
python3 -I scripts/install.py --check  # verify all roots match this repo
python3 -I scripts/doctor.py
python3 -I skills/ship-eval/scripts/evalctl.py run
```
`.github/workflows/validate.yml` runs the same install and checks on every push and PR.
READY means ready for your review — never publish without fresh explicit approval.
