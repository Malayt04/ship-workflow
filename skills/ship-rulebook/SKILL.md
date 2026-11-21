---
name: ship-rulebook
description: "Turn corrections into deterministic checks first, prose rules second. Use on 'add a rule', 'note this for next time', repeated defects, or ship-pipeline handoff. Proposes exact text, pauses for user approval, writes only approved rulebook files."
---

# Ship Rulebook

A correction that stays in one conversation will be repeated. A correction that
becomes a check or a written rule will not. Every user correction and every
agent self-review finding must land here or be explicitly dismissed.

## Locations

- Global: `~/.agents/AGENT_RULES.md`
- Per-repo: `<repo>/docs/agent-rules.md`, from `assets/repo-rules-template.md`

Never write a rule without user approval. Propose the exact diff, then apply
after agreement.

## Procedure

1. **Capture** in `.agent-work/<issue>/rulebook-candidates.md`: source (user /
   self-review / repeated defect), evidence (`file:line` or command output),
   desired behaviour, failure mode prevented, scope (global or repo).

2. **Classify**

| Type | Meaning | Action |
|---|---|---|
| Enforceable | linter, type, test or schema can catch it | rule **plus** a concrete check proposed for next `ship-review` |
| Judgment | needs taste or context | short imperative prose rule with rationale |
| One-off | specific to this ticket | no rule; log why |

Prefer enforceable. Comments and docs are not enforcement and never fix a
repeated mistake.

3. **Pause and propose** with `question`: show rule text, type, before/after
   diff; options approve-global / approve-repo / edit / reject. Present evidence
   first for self-review findings; never silently promote your own opinion.

```bash
L=~/.agents/skills/ship-loop/scripts/loopctl.py
python $L checkpoint <issue> --question "Approve R-0xx: <text>?"
python $L resume <issue> --note "rule approved"
```

4. **Apply approved rules** — one per finding, short and imperative:

```markdown
### R-012 — Never use raw file reads for HTTP in application code
- Type: enforceable (lint rule to add)
- Scope: repo — <repo>
- Source: issue #206 self-review, <file>:88 (2026-11-21)
- Rationale: bypasses proxying, timeouts and TLS handling.
- Good: <approved API>
- Bad: <banned pattern>
```

For enforceable rules, add the check to `review.md` so the next review catches
it automatically.

5. **Maintain** — deduplicate by pointing to the existing rule; track status
   (`proposed`, `approved`, `rejected`, `retired`) with date and decider; retire
   obsolete rules with date and reason.

At handoff, list every candidate and status in `handoff.md` and name applied
rule ids in the final message.
