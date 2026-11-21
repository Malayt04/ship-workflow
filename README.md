# agent-workflow

Shared, harness-neutral agent system (Claude Code, OpenCode, Codex): the `ship-*`
skills, their scripts, regression evals, and the global rulebook.

- `skills/ship-*` — pipeline stages (intake → implement → impact → requirements → review → verify → handoff), `ship-loop`, `ship-fastlane`, `ship-git`, `ship-eval`, `ship-rulebook`, `ship-teach`
- `scripts/` — `doctor.py` (system health), `validate-skills.py` (cross-root sync)
- `evals/` — deterministic regression cases (`manifest.json`, `fixtures/`)
- `AGENT_RULES.md`, `AGENTS.md` — rulebook and harness-wide instructions

Check health: `python3 -I scripts/doctor.py`

Publishing is gated: never push without explicit approval (`ship-git guard-push`).
