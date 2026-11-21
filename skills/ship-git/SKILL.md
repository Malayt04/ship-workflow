---
name: ship-git
description: "Use for every branch creation, commit, PR title, and any push/PR/deploy intent in any repository or harness. Enforces one standard: branches named <type>(<base>)/<slug>, PR titles <type>(<base>): <name>, conventional commits, and an explicit push-approval guard. Trigger on branch/commit/push/PR intent or automatically inside ship-pipeline."
---

# Ship Git

One Git standard across all harnesses, plus a guard around the only
irreversible action: publishing.

## Hard rule — never publish without approval

**Never push, PR, merge, or deploy without explicit user consent.** Broad local
access is not publishing consent. Local commits, branches, resets and deletes
are fine.

```bash
G=~/.agents/skills/ship-git/scripts/gitctl.py
python $G guard-push --issue <id>      # exit 2 without approval
# Token comes from the user, never from the agent:
export SHIP_APPROVAL_TOKEN='<user-supplied-token>'   # or chmod 600 ~/.agents/APPROVAL_TOKEN
python $G approve --issue <id> --by user --minutes 30
```

`approve` records the token fingerprint and expiry; `guard-push` refuses if the
token changes or is removed. `--by` is required and only `user` is accepted —
an agent cannot approve its own push. Hooks are optional; ask before installing.

## Standards

| Item | Form | Example |
|---|---|---|
| Branch | `<type>(<base>)/<kebab-slug>` | `feat(master)/add-vehicle-cpt` |
| Commit | `<type>: <lowercase imperative>` | `feat: add public vehicle CPT` |
| PR title | `<type>(<base>): <name>` | `feat(master): add public vehicle CPT` |

Types: `feat`, `fix`, `perf`, `chore`, `docs`, `refactor`, `test`, `build`,
`ci`, `style`, `revert`. Subject ≤72 chars, no trailing period, one change per
commit; optional scope (`fix(rest): ...`) and `!` for breaking changes.

Git refs cannot contain `:`, so branches use `/` before the slug. The colon is
reserved for PR titles.

```bash
python $G branch feat master add-vehicle-cpt --dry-run
python $G commit-msg --message "feat: add vehicle CPT"
python $G pr-title --title "feat(master): add vehicle CPT"
python $G install-hooks --repo /path/to/repo     # ask first
```

Drop `--dry-run` to create and switch the branch. Pipeline: stage 0 create
branch, stage 2 validate each commit, stage 7 handoff states
`NOT pushed, no PR opened` unless explicitly approved.

Every PR must target the default branch. CI checks `github.base_ref`; local
checks can use `python $G check-pr-base --pr <number>` or `--base <branch>`.
Stacked PRs merge into intermediate branches and leave the default branch
behind, so they are rejected (R-014).
