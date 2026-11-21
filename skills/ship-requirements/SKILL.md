---
name: ship-requirements
description: "Prove every acceptance criterion is met and no scope creep slipped in. Use after implementation and impact analysis, or ship-pipeline stage 4. Produces traceability.md mapping ACs to code, checks, and runtime evidence."
---

# Ship Requirements

A mechanical comparison of what was asked to what was built — not a vibe check.
Inputs: `spec.md`, `impact.md`, and the full diff. Re-read the issue if the spec
may have drifted.

## Traceability matrix

For each `AC-n`, record implementation file:line, automated check (test/lint/
type), runtime evidence (CLI/HTTP/browser), and status: `met`, `partial`,
`unmet`, or `out-of-scope (approved)`. Both implementation reference and
verification method are required for `met`; implemented-but-unverified is
`partial`.

## Scope creep

List every meaningful change mapping to no AC. For each: necessary enabler
(explain why) or unrequested work (remove it or get approval). "While I was
here" refactors are creep unless the spec lists them.

## Impact cross-check

Every high-risk item in `impact.md` needs a verification row. A consumer found
by impact but not covered here is a gap — add a row or return to implementation.

## Template — `.agent-work/<issue>/traceability.md`

```markdown
# Traceability — <id>
| AC | Requirement | Implementation | Automated check | Runtime evidence | Status |
|----|-------------|----------------|-----------------|------------------|--------|

## Scope creep review
| Change | Maps to AC? | Decision | Rationale |
|---|---|---|---|

## Impact cross-check
<each high-risk item → row or gap>

## Gaps
<none | partial/unmet items and what is needed>
```

Gate: no `unmet`; every `partial` has reason and user approval; no unmapped
changes. Then `loopctl complete <issue> requirements`.
