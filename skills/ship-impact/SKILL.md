---
name: ship-impact
description: "Map the blast radius of every changed public symbol across the whole repo. Use after implementation or before a risky refactor, or ship-pipeline stage 3. Produces impact.md with verified consumers, risks, and mitigations."
---

# Ship Impact

Answer: *if this symbol changed, what else breaks?* Guessing is not allowed.
Every changed public contract needs verified consumers or a reproducible
"no consumers found" statement. Do a quick scan at intake for risky refactors;
the full scan runs against the actual diff.

## 1. Enumerate the change

```bash
git diff --stat; git diff --name-only; git diff -U0 | head -n 400
```

Identify changed functions, methods, types, constants, hooks/events, routes,
config keys, persisted data, CLI flags, exported components, CSS contracts, and
build targets.

## 2. Find consumers

Structural search first, text second; recipes in `references/languages.md`.
Search source, tests, fixtures, generated code, config, and docs — not just the
edited directory. For reflection, string-built hooks, DI, registries, or route
tables, say so explicitly and list possible producers; never claim "no
consumers".

## 3. Check boundaries

Read `<repo>/docs/agent-rules.md` and `~/.agents/AGENT_RULES.md`. Flag forbidden
boundary crossings, copied deprecated patterns, and new workarounds. A comment
justifying a hack is a finding, not an explanation.

## 4. Template — `.agent-work/<issue>/impact.md`

```markdown
# Impact — <id>
Changed files: <n> | Changed public symbols: <n>

## Symbol impact
| Symbol/contract | Defined at | Consumers (file:line) | Indirect | Risk | Mitigation | Verified by |
|---|---|---|---|---|---|---|

## Surfaces checked with no consumers
| Search | Query | Result |
|---|---|---|

## Architecture / rulebook check
<violations with file:line and rule id, or none>

## Residual risks
<dynamic dispatch, external consumers, untested paths>

## Affected areas confirmed
<sections/systems to re-verify in stage 6>
```

Gate: every public symbol appears in a table or the no-consumer list; each risk
has mitigation and verification; violations are fixed or filed as rulebook
candidates. Then `loopctl complete <issue> impact`.
