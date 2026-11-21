#!/usr/bin/env python3
"""Verify all ship-* skills and shared assets are identical across harness roots."""
from __future__ import annotations

import sys
from pathlib import Path

ROOTS = [
    Path.home() / ".config/opencode/skills",
    Path.home() / ".claude/skills",
    Path.home() / ".agents/skills",
]
SHARED = [
    "ship-loop/scripts/loopctl.py",
    "ship-git/scripts/gitctl.py",
    "ship-teach/scripts/teach-digest.py",
    "ship-eval/scripts/evalctl.py",
    "ship-fastlane/scripts/fastlane.py",
    "ship-review/references/stacks.md",
    "ship-verify/references/stacks.md",
    "ship-impact/references/languages.md",
]
SKILLS = sorted(
    p.name for p in ROOTS[0].glob("ship-*") if (p / "SKILL.md").is_file()
)


def main() -> int:
    problems = []
    for name in SKILLS:
        canonical = (ROOTS[0] / name / "SKILL.md").read_text()
        if not canonical.startswith("---\n") or "\ndescription:" not in canonical:
            problems.append(f"{name}: malformed frontmatter")
        for root in ROOTS[1:]:
            path = root / name / "SKILL.md"
            if not path.is_file() or path.read_text() != canonical:
                problems.append(f"{name}: differs in {root}")
    for rel in SHARED:
        canonical = (ROOTS[0] / rel).read_text()
        for root in ROOTS[1:]:
            path = root / rel
            if not path.is_file() or path.read_text() != canonical:
                problems.append(f"{rel}: differs in {root}")
    print(f"skills: {len(SKILLS)} | shared assets: {len(SHARED)} | roots: {len(ROOTS)}")
    if problems:
        for item in problems:
            print("MISMATCH", item)
        return 1
    print("RESULT: ALL IN SYNC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
