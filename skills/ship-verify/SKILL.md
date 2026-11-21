---
name: ship-verify
description: "Prove a change works at runtime with saved output. Use before handoff or ship-pipeline stage 6. Backend, WP-CLI, browser, library and platform recipes in references/stacks.md. Produces verification.md with evidence and the verify gate."
---

# Ship Verify

Move from "the diff looks right" to "I ran it; here is the output". Spend most
effort here. The user reviews evidence, not claims.

## Pick checks by change type

Prove every AC in `spec.md` and every residual risk in `review.md`. Use
`references/stacks.md` for stack commands.

- **Backend / API / CLI** — start with test config; assert status, headers, body
  with `curl`, `jq`, `rg`.
- **WordPress** — `php -l`, then WP-CLI smoke checks against local/wp-env/
  Playground; clean up smoke content.
- **Frontend / UI** — serve locally; `curl | rg` for markup; Playwright or
  `chrome-devtools-axi` for interaction, screenshots, console errors, mobile
  width, keyboard access.
- **Library / algorithm** — focused unit tests plus boundary, empty and
  idempotency cases.
- **Migration / cron** — dry run, assert pre/post state, run twice. Never
  destructive commands on a remote environment.
- **Platform diagnostics** — read-only only (`vip @app.env logs`, `slowlogs`).
  No deploys, purges or remote writes.

## Procedure

1. For each AC/risk choose a concrete check with an expected result.
2. Run it; save actual output verbatim. Never write "passed" without output.
3. On failure, fix code in implementation — don't just rerun — then rerun
   impact → requirements → review → verify.
4. Unavailable tool → mark `BLOCKED` and say what is needed. Blocked critical
   checks are not passes.

## Template — `.agent-work/<issue>/verification.md`

```markdown
# Verification — <id>
Environment: <local/wp-env/playground> | Stack: <stack>

| ID | Criterion/risk | Check | Expected | Actual | Result | Evidence |
|----|----------------|-------|----------|--------|--------|----------|

Screenshots / traces: <paths>
## Failed / blocked checks
<none | details>
## Summary
<passed>/<total> passed; <n> blocked; residual risks: <list>
```

Gate: `loopctl gate <issue> verify --passed --evidence <file>` only when every
critical check passed and evidence paths exist; otherwise `--failed`.
