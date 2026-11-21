#!/usr/bin/env python3
"""Detect a project's stack from manifest files and suggest a ship adapter."""
from __future__ import annotations

import argparse
from pathlib import Path

RULES = [
    ("composer.json", "php"),
    ("package.json", "node"),
    ("go.mod", "go"),
    ("Cargo.toml", "rust"),
    ("pyproject.toml", "python"),
    ("requirements.txt", "python"),
    ("setup.py", "python"),
]


def detect(root: Path) -> tuple[str, str]:
    for filename, stack in RULES:
        path = root / filename
        if path.is_file():
            return stack, filename
    return "unknown", "none"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="project root to inspect")
    args = parser.parse_args()
    root = Path(args.cwd).expanduser().resolve()
    stack, manifest = detect(root)
    print(f"STACK: {stack}")
    print(f"MANIFEST: {manifest}")
    print(f"ADAPTER: references/stacks/{stack}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
