# Stack recipes — review and verification

Detect the stack from repo manifests before choosing commands:
`composer.json`, `go.mod`, `Cargo.toml`, `package.json`, `pyproject.toml`,
`Gemfile`, `Makefile`, `.csproj`. Run the repo's own scripts when present.

## WordPress / PHP

```bash
php -l path/to/changed.php                       # each changed file
vendor/bin/phpcs --report=full <changed files>   # project ruleset (WP + VIP where applicable)
composer run phpstan                            # or vendor/bin/phpstan analyse
composer run test                               # or vendor/bin/phpunit
```

Use `wp-phpstan` for config/baseline rules. Runtime smoke checks (WP-CLI,
curl, Playwright) belong in `ship-verify/references/stacks.md`.

## Go

```bash
go build ./...
go test ./...
go vet ./...
golangci-lint run ./...        # if configured
gofmt -l <changed files>       # must print nothing
```

## Rust

```bash
cargo build --all-targets
cargo test --all-targets
cargo clippy --all-targets -- -D warnings    # if configured
cargo fmt --check
```

## JavaScript / TypeScript (Node or frontend)

```bash
npm test            # or pnpm test / yarn test
npm run lint        # ESLint / Biome
npx tsc --noEmit    # when TypeScript is present
npm run build
```

## Python

```bash
python -m pytest
ruff check <changed files>
mypy <changed files>       # if configured
python -m compileall -q <changed files>
```

## Universal fallback

If no stack tooling exists, at minimum prove: syntax/parse check, a focused
functional test, and a runtime smoke check via `ship-verify`. Report missing
tooling as `NOT CONFIGURED`; never silently skip a check.
