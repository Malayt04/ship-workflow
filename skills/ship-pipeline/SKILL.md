---
name: ship-pipeline
description: "Mandatory end-to-end delivery loop for ANY code-changing task in ANY stack. Invoke on fixes, features, refactors and PRs, even from a one-line request. Runs intake → implement → impact → requirements → review → verify → handoff with deterministic gates. Small low-risk changes route to ship-fastlane. Never push, open a PR, or message before READY."
---

# Ship Pipeline

Trust comes from evidence, not speed. The user reviews artifacts, not a diff.
Prove four things: asked-for behaviour (`spec.md` → `traceability.md`), known
blast radius (`impact.md`), review passed (`review.md`), runtime works
(`verification.md`).

## Routing

1. Detect the stack from manifests: `composer.json`, `go.mod`, `Cargo.toml`,
   `package.json`, `pyproject.toml`, `Makefile`.
2. Run `fastlane.py check`. If eligible, hand off to `ship-fastlane` and stop.
3. Otherwise use this pipeline. Stack commands live in each stage's
   `references/stacks.md`; never hardcode WordPress commands into a generic stage.

## Hard gates

- Isolated git worktree; branch `<type>(<base>)/<slug>` via `ship-git branch`.
  PR title, if ever approved: `<type>(<base>): <name>` via `ship-git pr-title`.
- **Never push, PR, merge, or deploy** without explicit post-handoff consent.
  `ship-git guard-push` must pass first.
- Every stage transition via `loopctl`; failed gate → `loopctl fail`, back to
  implementation. Never wave a gate through.
- Message only on a checkpoint (design decision, rulebook approval) or final
  handoff. Budget: 3 small, 6 feature, 10 cross-cutting.
- Correction → deterministic check or architectural fix. Prose rules only for
  judgment calls. Missing intent → stop and ask.

## Artifacts — `.agent-work/<issue-id>/`

```
loop-state.json   spec.md        impact.md      traceability.md
review.md         verification.md evidence/     handoff.md
rulebook-candidates.md
```

## Stages

| # | Stage | Skill | Exit |
|---|-------|-------|------|
| 0 | Prepare | `ship-git`, `ship-loop` | worktree, branch, loop initialised, stack detected |
| 1 | Intake | `ship-intake` | `spec.md`, decisions locked |
| 2 | Implement | domain skill | code change, `loopctl complete implement` |
| 3 | Impact | `ship-impact` | `impact.md` |
| 4 | Requirements | `ship-requirements` | `traceability.md` |
| 5 | Review | `ship-review` | `review.md`, `review` gate |
| 6 | Verify | `ship-verify` | `verification.md`, `verify` gate |
| 7 | Handoff | `ship-rulebook` | `handoff.md`, `loopctl handoff` |

If any `ship-*` skill or script changed, run `ship-eval run` in stage 6 and
attach `~/.agents/evals/last-report.md`.

## Handoff template

```markdown
## Handoff — <id>: <title>
- Status: ready for your review
- Worktree / branch: <path> / <branch>
- Stack: <stack>
- Artifacts: spec, impact, traceability, review (P0–P3 counts), verification (n/n), evidence/
- Loop: <used>/<budget>
- Rulebook candidates: <none | list>
- Needs your decision: <list>
- NOT pushed, no PR opened.
```

## Failure handling

- Failed gate → fix in implementation, rerun all downstream stages.
- Missing decision → `loopctl checkpoint --question "..."`, then `resume`.
- Tool unavailable → mark `BLOCKED`; blocked critical check is not a pass.
- Budget exhausted → `ESCALATED`; stop and message with artifacts and blocker.
