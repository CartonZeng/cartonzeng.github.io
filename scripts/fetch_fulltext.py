#!/usr/bin/env python3
"""Download arXiv PDFs and extract full text (references stripped) for the word cloud.

    python scripts/fetch_fulltext.py

Writes ``data/fulltext/<arxiv-id>.txt``. Re-run after adding a paper to PAPERS
in ``generate_wordcloud.py`` (or pass IDs on the command line).
"""

from __future__ import annotations

import re
import sys
import tempfile
import urllib.request
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "data" / "fulltext"

# Keep in sync with scripts/generate_wordcloud.py PAPERS
DEFAULT_IDS = [
    "2609.22758",
    "2604.08647",
    "2412.14621",
    "2310.09910",
    "2110.00259",
    "1808.00357",
    "2605.24174",
    "2504.13004",
    "2402.01604",
    "2601.23264",
    "2403.09597",
    "2305.05067",
    "2205.02957",
    "2206.12425",
    "1711.05210",
]


def strip_references(text: str) -> str:
    """Drop the bibliography (and everything after it)."""
    m = re.search(r"\n\s*(?:references|bibliography)\s*\n", text, re.IGNORECASE)
    if m:
        return text[: m.start()].rstrip()
    # revtex often has no heading; entries start at [1] in the back half
    m = re.search(r"\n\[1\]\s", text)
    if m and m.start() > 0.5 * len(text):
        return text[: m.start()].rstrip()
    return text.rstrip()


def fetch_one(aid: str) -> Path:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / f"{aid}.txt"
    pdf_path = Path(tempfile.gettempdir()) / f"wc_{aid}.pdf"
    url = f"https://arxiv.org/pdf/{aid}"
    print(f"  download {aid} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (wordcloud-fetch)"})
    data = urllib.request.urlopen(req, timeout=180).read()
    pdf_path.write_bytes(data)
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    text = strip_references(text)
    out.write_text(text + "\n", encoding="utf-8")
    print(f"  wrote {out.relative_to(ROOT)}  ({len(text):,} chars)", flush=True)
    return out


def main() -> None:
    ids = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_IDS
    print(f"fetching {len(ids)} papers into {OUTDIR.relative_to(ROOT)}")
    failed = []
    for aid in ids:
        try:
            fetch_one(aid)
        except Exception as exc:  # noqa: BLE001 — report and continue
            failed.append((aid, str(exc)))
            print(f"  FAIL {aid}: {exc}", flush=True)
    if failed:
        print(f"\n{len(failed)} failed:")
        for aid, err in failed:
            print(f"  {aid}: {err}")
        raise SystemExit(1)
    print("done")


if __name__ == "__main__":
    main()
