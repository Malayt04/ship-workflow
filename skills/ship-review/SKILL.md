---
name: ship-review
description: "Review a completed change: run mechanical checks then a defect-first architectural review. Use before verification or ship-pipeline stage 5. Read-only; writes review.md with P0–P3 findings. Stack commands in references/stacks.md."
---

# Ship Review

Two passes, one artifact. Machines find what they can prove; the agent reviews
architecture, intent, security, performance, and rulebook adherence. Read-only:
findings return to implementation, never fixed here.

## Pass A — mechanical

Detect tooling from `composer.json`, `go.mod`, `Cargo.toml`, `package.json`,
`pyproject.toml`, `Makefile`, then follow `references/stacks.md`. Run formatter
(check mode), linter, static analysis, tests, build. Save raw output under
`evidence/checks/`; record command, exit code, summary. Missing tool =
`NOT CONFIGURED`, never silently skipped. No baselining or suppressing newly
introduced errors.

## Pass B — defect-first

Invoke `review-agent` with the full diff, `spec.md`, `impact.md`, and both
rulebooks. Report only defects introduced by this change, each with a
demonstrable scenario, ordered P0–P3. No speculation, no style nits. If the
skill is unavailable, apply the same criteria inline.

Universal layers:

- **Intent** — matches `spec.md`; no silent behaviour change.
- **Architecture** — boundaries, dependency direction, established patterns;
  no new workaround where a design fix belongs.
- **Security** — validation, authorization, injection, secrets, deserialization,
  traversal, CSRF where applicable.
- **Performance** — N+1, unbounded loops/queries, hot-path allocations, cache
  invalidation.
- **Compatibility** — signatures, responses, versioning, migrated callers/data.
- **UI** — accessibility, keyboard, i18n, responsive.
- **Rulebook** — cite rule id for every violation.

Stack specifics: `references/stacks.md` and the relevant domain skill.

## Template — `.agent-work/<issue>/review.md`

```markdown
# Review — <id>
## Findings
[P1] Imperative title — path:line
<scenario and why it is wrong, inside the reviewed diff>

## Mechanical checks
| Check | Command | Exit | Summary | Evidence |
|---|---|---|---|---|

## Architecture assessment
<specifics>

## Rulebook violations
| Rule id | Source | Where | Status |
|---|---|---|---|

## Test gaps
<behaviour with no automated check>

## Residual risks
<what review cannot prove; hand to stage 6>
```

Gate: no P0/P1, checks pass (or documented pre-existing failures), violations
fixed or user-approved. Pass with `loopctl gate <issue> review --passed
--evidence <pass-file>`; otherwise `--failed` and return to implementation.
