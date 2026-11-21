#!/usr/bin/env python3
"""Verify local Markdown links resolve; remote URLs and anchors are ignored."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_DIRS = {".git", ".agent-work", "fixtures", "__pycache__"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    tracked = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=root, capture_output=True, text=True, check=False
    )
    if tracked.returncode == 0 and tracked.stdout.strip():
        files = [
            root / line for line in tracked.stdout.splitlines()
            if not any(part in SKIP_DIRS for part in Path(line).parts)
        ]
    else:
        files = [
            path for path in root.rglob("*.md")
            if not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
        ]
    checked = 0
    problems: list[str] = []
    for path in files:
        for raw in LINK_RE.findall(path.read_text(errors="replace")):
            target = raw.strip().split()[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if "://" in target:
                continue
            checked += 1
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                problems.append(f"{path.relative_to(root)} -> {target}")

    if problems:
        print(f"DOC LINKS FAIL: {len(problems)} broken")
        for item in problems[:20]:
            print(f"  {item}")
        return 1
    print(f"DOC LINKS OK: {len(files)} files, {checked} local links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
