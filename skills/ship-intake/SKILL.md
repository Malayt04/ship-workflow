---
name: ship-intake
description: "Read the issue and lock every design decision before code is written. Use on issue links, bug reports, feature requests, or ship-pipeline stage 1. Produces spec.md with testable acceptance criteria; never implement with unresolved intent."
---

# Ship Intake

Turn a messy issue into an unambiguous contract used by requirements, review,
and verification. Guessing intent produces slop.

## 1. Load the source

Include comments; decisions hide there.

```bash
gh issue view <n> --json title,body,labels,comments,url \
  --jq '"\(.title)\n\(.body)\nCOMMENTS:\n\(.comments[] | "--- \(.author.login): \(.body)")\n\(.url)"'
```

Use `gh-axi issue` when available; `webfetch` for URLs; pasted text verbatim.
Never invent details.

## 2. Find ambiguity

List every decision the issue does not make:

- user-visible behaviour and edge cases (empty, error, denied)
- data model, migrations, backfill, persisted format
- compatibility: APIs, URLs, hooks, config, existing consumers
- versions and new dependencies
- UI scope, a11y, i18n, responsive
- rollout: flags, environments, cache invalidation, observability
- explicit out-of-scope items

## 3. Ask once, in a batch

Use `question`; 2–4 concrete options, recommended first with `(Recommended)`.
Ask about decisions, not facts discoverable by reading code. Do not code while
anything is unanswered. Deferrable items need an owner, a trigger, and explicit
agreement.

## 4. Write `.agent-work/<issue>/spec.md`

```markdown
# Spec — <id>: <title>
Source: <url | pasted in chat> | Stack: <detected>

## Problem
<one paragraph, user's terms>

## Outcome
<what success looks like>

## Acceptance criteria
- [ ] AC-1 — <observable, testable behaviour>

## Design decisions
| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|

## Constraints
<platform, versions, compatibility, security, performance>

## Out of scope
<excluded work and why>

## Affected areas (initial guess)
<likely modules, routes, templates>

## Verification plan
<how each AC will be proven>

## Open questions
<none | question, owner, trigger>
```

Gate: at least one AC, all decisions answered or deferred with agreement, each
AC has a plausible verification method. Then `loopctl complete <issue> intake`.
