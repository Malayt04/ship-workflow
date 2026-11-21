# Symbol search recipes by language

Always search the **whole repository** — source, tests, fixtures, generated
code, config, and docs. Use structural search where available, text search to
confirm. Record the exact query used for "no consumers found" claims.

## Generic

```bash
# text search for a symbol across common source types
rg -n '\bSymbolName\b' -t php -t go -t rs -t js -t ts -t py
# AST search when ast-grep is available
ast-grep -p '$OBJ.$METHOD($$$ARGS)' -t js
```

## PHP / WordPress

```bash
rg -n "function\s+foo\s*\(" -t php
rg -n "\bfoo\s*\(" -t php -t js
rg -n "add_(action|filter)\(\s*['\"]hook_name" -t php
rg -n "register_(post_type|taxonomy|rest_route|block_type)" -t php
wp post-type list; wp taxonomy list; wp rewrite list; wp cron event list
```

## Go

```bash
rg -n 'func (\(.*\) )?Foo\(' -t go
rg -n '\bFoo\(' -t go
rg -n 'type Foo (struct|interface)' -t go
go list -deps ./...        # package-level dependencies
```

## Rust

```bash
rg -n 'fn foo\b|pub fn foo\b' -t rs
rg -n '\bfoo\(' -t rs
rg -n 'impl.*Foo|trait Foo' -t rs
cargo tree                 # crate-level dependencies
```

## JavaScript / TypeScript

```bash
rg -n '(function|const|let|var)\s+foo\b' -t js -t ts
rg -n '\bfoo\(' -t js -t ts -t jsx -t tsx
rg -n "from ['\"].*foo|require\(['\"].*foo" -t js -t ts
```

## Python

```bash
rg -n 'def foo\s*\(' -t py
rg -n '\bfoo\(' -t py
rg -n 'class Foo\b' -t py
```

## Dynamic dispatch caveat

If a symbol can be reached via reflection, a hook name built from a string,
dependency injection, or a plugin/extension registry, say so explicitly and
list the places that could produce it. Never claim "no consumers" in that case.
