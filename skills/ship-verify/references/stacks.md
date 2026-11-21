# Stack recipes — runtime verification

Runtime verification proves behaviour, not just syntax. Choose the checks that
match the change type; save raw output to `evidence/`.

## Backend API / service (any language)

- Start the service locally with its test configuration.
- Exercise the changed route/function: `curl -sS -i <url>` or the language's
  client (`go run ./cmd/...`, `cargo run`, `npm run dev`, `python -m ...`).
- Assert status code, headers, and body with `rg`/`jq`.
- Check logs for errors emitted during the request.

## WordPress / PHP

```bash
php -l path/to/changed.php
wp post-type list
wp post-type get <cpt> --fields=name,label,public
wp taxonomy list
wp option get <option_name>
wp post create --post_type=<cpt> --post_title='Smoke test' --porcelain
wp cron event list | rg '<hook>'
wp eval 'echo rest_do_request("/wp-json/<ns>/<route>")->get_status();'
```

Use `wp-env`, a local WP, or `wp-playground` for a shareable preview. Clean up
smoke-test content. Read-only VIP diagnostics (`vip @app.env logs`, `slowlogs`)
are allowed; deploys, cache purges, and remote writes are not.

## Go

```bash
go test ./... -run '<TestName>' -v
go run ./cmd/<app> --config config/test.yaml &
curl -sS -i http://localhost:<port>/<route>
```

## Rust

```bash
cargo test <test_name> -- --nocapture
cargo run -- --config config/test.toml &
curl -sS -i http://localhost:<port>/<route>
```

## JavaScript / TypeScript frontend

- Serve locally (`npm run dev`, Vite, Next, Storybook, wp-env, Playground).
- Fast assertion: `curl -sS <url> | rg 'expected-markup|data-attr|aria-label'`.
- Playwright MCP tools when available (navigate, snapshot, screenshot, console
  errors); otherwise `npx playwright` or `chrome-devtools-axi open <url>`.
- Check desktop + mobile widths, interactive states, keyboard access, console
  and network errors. Save screenshots/traces to `evidence/`.

## Python

```bash
python -m pytest <test_file> -v
python -m <module> --config config/test.toml &
curl -sS -i http://localhost:<port>/<route>
```

## Data migrations / options / cron (any stack)

Dry-run where possible, assert pre/post state, and run twice to prove
idempotency. Never run a destructive command against a remote environment.
