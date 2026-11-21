# Global Agent Rules

Mandatory for every agent in every repository and harness. Add or change rules
only through the `ship-rulebook` skill and only with explicit user approval.
Repo-specific rules live in `<repo>/docs/agent-rules.md`.

These rules come from the "All Code Is Slop (Except Mine)" review (2026-11-21)
and the user's stated goal: earn high trust by turning every correction into a
deterministic guardrail, not by prompting harder.

## Hard rules — never

### R-001 — Turn every correction into a deterministic check or an architectural fix
- Type: judgment (enforced by pipeline gate)
- Source: video review + user direction, 2026-11-21
- Rationale: a correction that lives only in chat is forgotten by the next agent.
  A lint rule, type, test, or API redesign is reproducible and can be trusted.
- Good: add a PHPCS sniff / PHPStan rule / test when the agent misuses an API.
- Bad: "remember not to do that" in a prompt or a code comment.

### R-002 — Do not treat comments or docs as enforcement
- Type: judgment
- Source: video — agents write comments justifying hacks; comments go stale.
- Rationale: prose cannot fail a build. Only machine-checked rules are reliable.
- Good: an error message on the lint rule that explains the root-cause fix.
- Bad: a comment saying "do not use setTimeout here".

### R-003 — Clean existing violations when adding a new guardrail
- Type: judgment
- Source: video — codebase is a garden; agents copy whatever looks established.
- Rationale: a new rule with legacy violations left in place leaves the bad
  pattern as the visible example for the next agent.
- Good: add the sniff, then fix or narrowly baseline all existing hits.
- Bad: add the sniff and leave 40 violations for "later".

### R-004 — Keep prose rules to genuine judgment calls
- Type: judgment
- Source: video — trust pyramid, top layer only.
- Rationale: architecture intent and UX trade-offs need explanation; mechanical
  mistakes do not. Prose rules should be the smallest layer.

### R-005 — Never declare a task done without review and runtime evidence
- Type: enforceable by pipeline
- Source: user direction, 2026-11-21
- Rationale: the user reviews artifacts, not diffs. `review.md` and
  `verification.md` must exist with passing critical checks before handoff.

### R-006 — Never push, open a PR, merge, or deploy without explicit user approval
- Type: enforceable (`ship-git guard-push`)
- Source: global `AGENTS.md` §1, user emphasis 2026-11-21
- Rationale: local commits, branches and deletions are recoverable; once
  something is pushed it is out there. Broad local access is **not** publishing
  consent. Each publishing action needs fresh, explicit approval.
- Good: ask, record approval with `ship-git approve --issue <id>`, then publish.
- Bad: assuming a previous approval or a permissive environment covers this push.

### R-007 — Never self-approve an agent's own work
- Type: enforceable
- Source: video + user direction
- Rationale: an agent proposing a rule about its own mistake must discuss it with
  the user first (see `ship-rulebook`).

### R-008 — Never write a rulebook entry without user approval
- Type: enforceable
- Source: user direction, 2026-11-21
- Rationale: the rulebook is the constitution; only the user ratifies it.

### R-009 — Finish the loop before messaging the user
- Type: enforceable (ship-loop controller: status must be READY)
- Scope: global — all harnesses, all stacks
- Source: 2026-11-21 user request for loop engineering
- Rationale: progress chatter erodes trust; a bounded loop with explicit checkpoints keeps the agent working until evidence is complete.
- Good: run stages via loopctl; message only on checkpoint, escalation, or final handoff.
- Bad: send interim updates, or declare done without READY.

### R-010 — One Git standard across all harnesses
- Type: enforceable (`ship-git branch` / `ship-git commit-msg`)
- Scope: global — every repository and harness
- Source: user direction, 2026-11-21
- Rationale: inconsistent commit and branch formats make history unreadable and
  review slow. A single validator removes harness-specific guessing.
- Branch: `<type>(<base>)/<slug>`, e.g. `feat(master)/add-vehicle-cpt`. Git refs
  cannot contain `:`, so branches use `/` and PR titles use `:`.
- Commit: `feat:`, `fix:`, `perf:`, `chore:`, `docs:`, `refactor:`, `test:`,
  `build:`, `ci:`, `style:`, `revert:` — lowercase imperative subject, <= 72
  chars, no trailing period.
- PR title: `<type>(<base>): <name>`, e.g. `feat(master): add vehicle CPT` —
  validated with `ship-git pr-title` before any PR is opened.

### R-011 — Repeated work becomes a script
- Type: enforceable (`doctor.py`, `validate-skills.py`, `evalctl`)
- Scope: global — any task done more than once
- Source: user direction, 2026-11-21
- Rationale: retyping the same check wastes tokens and drifts. A script is one
  deterministic artefact that can be run at any time and improved once.
- Good: on noticing a recurring check, write it under `~/.agents/scripts/` and
  call it thereafter.
- Bad: recreate the same ad-hoc validation script in a temp folder again.

### R-012 — Fast lane for small changes
- Type: enforceable (`fastlane.py check`, `loopctl --compact`)
- Scope: global — ≤2 files, ≤40 changed lines, no risky path, no design question
- Source: user approval, 2026-11-21
- Rationale: full ceremony on a typo is waste; skipping proof on a risky change
  is worse. The gate decides, not the agent's mood.
- Good: run `ship-fastlane`, one `fastlane.md`, 2 iterations, same no-push gate.
- Bad: use the fast lane to dodge impact analysis or runtime verification.

## Required practices — always

- Run `ship-pipeline` for every file-changing task, in stage order; route
  eligible small changes to `ship-fastlane` after `fastlane.py check`.
- Work in an isolated git worktree.
- Write artifacts under `.agent-work/<issue-id>/` and link them in handoff.
- Ask all design questions before implementing; never guess intent.
- Use `ship-impact` to find every consumer of a changed symbol.
- Use `ship-verify` to prove behaviour with WP-CLI, curl, Playwright, or
  chrome-devtools-axi, and save the output as evidence.
- Use `ship-git` for branches, commits, PR titles and the push guard; use
  `ship-teach` at the end of the day to turn the work into learning material for
  the user.
- Run `ship-eval` after every skill/script/rulebook edit; no skill change is READY
  with failing evals. Run `evalctl doctor` for the full health check. Loop health
  is visible via `loopctl telemetry`.
- Turn any repeated check into a script under `~/.agents/scripts/` (R-011).

## Rule ledger

| ID | Date | Status | Decider | Note |
|----|------|--------|---------|------|
| R-001…R-008 | 2026-11-21 | approved | user | seeded from video review and user direction |
| R-009 | 2026-11-21 | approved | user | finish the ship-loop before messaging; only checkpoint/escalate early |
| R-010 | 2026-11-21 | approved | user | one Git branch/commit standard across all harnesses; push still needs approval |
| R-011 | 2026-11-21 | approved | user | repeated work becomes a reusable script |
| R-012 | 2026-11-21 | approved | user | gated fast lane for small, low-risk changes |
| R-013 | 2026-11-21 | approved | user | publish approval requires a user-supplied token; agent self-approval is rejected |

## Retired rules

<!-- rule id, date retired, reason -->
