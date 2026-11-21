#!/usr/bin/env python3
"""Install or verify ship-* skills and shared tooling in harness roots."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = [
    Path.home() / ".config/opencode/skills",
    Path.home() / ".claude/skills",
    Path.home() / ".agents/skills",
]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
# Only ship-* directories are copied; third-party skills in each root are left alone.
# Shared tooling is merged so local generated files (e.g. last-report.md) survive.


def skill_names(source: Path) -> list[str]:
    return sorted(p.name for p in source.glob("ship-*") if (p / "SKILL.md").is_file())


def same_tree(a: Path, b: Path) -> bool:
    if not b.is_dir():
        return False
    afiles = {p.relative_to(a): p for p in a.rglob("*") if p.is_file()}
    bfiles = {p.relative_to(b): p for p in b.rglob("*") if p.is_file()}
    if afiles.keys() != bfiles.keys():
        return False
    return all(afiles[k].read_bytes() == bfiles[k].read_bytes() for k in afiles)


def sync_dir(src: Path, dst: Path, dry: bool, check: bool, label: str) -> list[str]:
    problems: list[str] = []
    if check:
        if not same_tree(src, dst):
            problems.append(f"{label}: differs from {src}")
    elif dry:
        print(f"DRY RUN: {label} -> {dst}")
    elif src.resolve() != dst.resolve():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE)
        print(f"INSTALLED {label} -> {dst}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-skills", type=Path, default=REPO / "skills")
    parser.add_argument("--source-scripts", type=Path, default=REPO / "scripts")
    parser.add_argument("--source-evals", type=Path, default=REPO / "evals")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--root", type=Path, action="append", help="override harness skill roots")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    roots = args.root or DEFAULT_ROOTS
    # Explicit roots are intentional; --home is a shortcut for isolated test installs.
    if args.home != Path.home():
        roots = [args.home / ".config/opencode/skills", args.home / ".claude/skills", args.home / ".agents/skills"]
    names = skill_names(args.source_skills)
    if not names:
        print("ERROR: no ship-* skills found in source", file=sys.stderr)
        return 2

    problems: list[str] = []
    for root in roots:
        for name in names:
            problems += sync_dir(args.source_skills / name, root / name, args.dry_run, args.check, name)

    agents = args.home / ".agents"
    for src, label in ((args.source_scripts, "scripts"), (args.source_evals, "evals")):
        problems += sync_dir(src, agents / label, args.dry_run, args.check, label)

    if args.check:
        if problems:
            for item in problems:
                print("MISMATCH", item)
            return 1
        print(f"IN SYNC: {len(names)} skills across {len(roots)} roots")
        return 0

    if args.dry_run:
        print(f"DRY RUN: {len(names)} skill(s) -> {len(roots)} root(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
