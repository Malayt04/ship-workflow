---
name: ship-teach
description: "Turn the day's agent work into engineering learning: commits, .agent-work artifacts and loop telemetry become a dated document with lessons, guardrails and teach-back questions. Use at end of workday or on 'teach me', 'daily learnings', 'summarise today's agent work'. Read-only toward product code; never pushes or opens PRs."
---

# Ship Teach

The goal is to ship code **and learn the engineering**. Convert a day of agent
activity into material the user can study: what changed, why, what broke, and
which decisions to remember. No product-code edits, no publishing.

## 1. Collect

```bash
python ~/.agents/skills/ship-teach/scripts/teach-digest.py \
  --since YYYY-MM-DD --repo /path/to/repo-a --repo /path/to/repo-b \
  --out ~/.agents/learning/YYYY-MM-DD-digest.md
```

Digest includes loop telemetry (counts, statuses, loop-back reasons) and per
repo: commits, uncommitted changes, and summaries of `.agent-work/<id>/`
artifacts. If repos are unnamed, ask once or use those listed in global
`AGENTS.md`.

## 2. Synthesise

Read the digest and referenced artifacts. List commits only as evidence; group
findings by theme. Extract:

- the engineering idea (blast-radius analysis, evidence gates, idempotent
  migrations, cache invalidation),
- the mistake caught and the deterministic guardrail that now prevents it,
- user decisions future agents must remember,
- one concept worth revising, with today's concrete example.

Three or four solid lessons beat ten "agent did X" bullets. Never invent a
lesson the artifacts do not support.

## 3. Write `~/.agents/learning/YYYY-MM-DD.md`

```markdown
# Engineering learnings — YYYY-MM-DD
## Today at a glance
| Change | Type | Outcome | Lesson id |
|---|---|---|---|
## Lessons learned
### L-1 — <principle>
- From: <repo, issue id, artifact>
- What happened / Why it matters / Apply it
## Mistakes caught and guardrails added
| Finding | Guardrail | Rule / check id |
|---|---|---|
## Decisions worth remembering
<decision + rationale>
## Teach-back — answer without looking
1. <test understanding>  2. <test a trade-off>  3. <test a guardrail>
## Exercises
- <small task reusing a principle in a new context>
## Open loops
<deferred decisions, blocked checks>
```

## 4. Hand off

State the document path and three key lessons. Route rulebook candidates
through `ship-rulebook` for approval. Weekly rollup: `--since <monday>`, title
`weekly-YYYY-Www.md`, add "what changed in my understanding".
