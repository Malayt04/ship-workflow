---
name: ship-fastlane
description: "Use for small, low-risk code changes that do not need the full ship-pipeline: typo/docs fixes, one-line config, a single test, formatting. Enforces a deterministic eligibility check, a 2-iteration compact loop (one fastlane.md), mechanical check plus runtime proof, and the same no-push rule. Trigger on 'fast lane', 'small fix', 'quick change', or when ship-pipeline stage 0 finds the change ineligible for the full pipeline."
---

# Ship Fast Lane

## Eligibility — all must hold

- At most **2 files** changed and at most **40 changed lines**.
- No migration, schema, auth, permissions, security, secrets, billing, deploy,
  or infrastructure path.
- Public API, data shape, and behaviour are unchanged.
- No design question is open.

If any check fails, use `ship-pipeline`. Do not argue your way around the gate.

```bash
python ~/.agents/skills/ship-fastlane/scripts/fastlane.py check --files a.py b.py
# ELIGIBLE: 2 file(s), 12 changed lines
```

Without `--files`, the check reads the current git diff.

## Procedure

1. `loopctl.py init <issue> --max-iterations 2 --compact`
2. `fastlane.py scaffold <issue>` — creates the one compact artifact.
3. Fill each section with **one to three lines**. No essays.
4. Run the repo's formatter/linter/test for the touched files. Save a pass line.
5. Run one runtime proof (CLI command, curl, unit test). Save the output.
6. Gate `review` and `verify` with the saved evidence; handoff from the same file.

```bash
python ~/.agents/skills/ship-loop/scripts/loopctl.py complete <issue> intake
python ~/.agents/skills/ship-loop/scripts/loopctl.py complete <issue> implement
python ~/.agents/skills/ship-loop/scripts/loopctl.py complete <issue> impact
python ~/.agents/skills/ship-loop/scripts/loopctl.py complete <issue> requirements
python ~/.agents/skills/ship-loop/scripts/loopctl.py gate <issue> review --passed --evidence <file>
python ~/.agents/skills/ship-loop/scripts/loopctl.py gate <issue> verify --passed --evidence <file>
python ~/.agents/skills/ship-loop/scripts/loopctl.py complete <issue> handoff
python ~/.agents/skills/ship-loop/scripts/loopctl.py handoff <issue>
```

`--compact` makes every `complete` check for a `## <stage>` heading in
`fastlane.md`. Missing heading means no advance.

## Non-negotiables

- Same hard gate as the full pipeline: no push, PR, merge, or deploy without
  explicit user approval.
- Failed check → `loopctl fail --reason "..."`, fix, re-run from `implement`.
- If the change grows beyond the gate, abandon the fast lane and start a full
  pipeline loop.
