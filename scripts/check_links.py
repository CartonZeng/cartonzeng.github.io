#!/usr/bin/env python3
"""Verify that every internal link, asset path and anchor in the site resolves.

    python scripts/check_links.py

Cheap substitute for the build-time checking a static site generator would give
us. Worth running before publishing and after renaming anything.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REF_PATTERN = re.compile(r'(?:href|src|data)="([^"]+)"')
ID_PATTERN = re.compile(r'id="([^"]+)"')


def main() -> int:
    pages = sorted(ROOT.glob("*.html"))
    if not pages:
        print("no pages found")
        return 1

    ids = {p.name: set(ID_PATTERN.findall(p.read_text(encoding="utf-8"))) for p in pages}
    problems: list[str] = []

    for page in pages:
        text = page.read_text(encoding="utf-8")
        for ref in REF_PATTERN.findall(text):
            if ref.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            if ref == "#":
                problems.append(f"{page.name}: placeholder link (href=\"#\")")
                continue

            path_part, _, fragment = ref.partition("#")

            if path_part:
                target = ROOT / path_part
                if not target.exists():
                    problems.append(f"{page.name}: missing file -> {path_part}")
                    continue
                owner = path_part
            else:
                owner = page.name

            if fragment and owner.endswith(".html") and fragment not in ids.get(owner, set()):
                problems.append(f"{page.name}: missing anchor -> {ref}")

    print(f"checked {len(pages)} pages: {', '.join(p.name for p in pages)}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for item in problems:
            print(f"  {item}")
        return 1

    print("all internal links, assets and anchors resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
