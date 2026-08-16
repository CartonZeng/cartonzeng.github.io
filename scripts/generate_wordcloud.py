#!/usr/bin/env python3
"""Build the publication word cloud for the Publications page.

    python scripts/generate_wordcloud.py

Corpus: the fourteen papers listed in the CV. Full text is read from
``data/fulltext/<arxiv-id>.txt`` (PDF text with the references section
stripped), falling back to ``data/abstracts/<arxiv-id>.txt`` and finally the
hard-coded title below when the full text has not been collected.

First-author papers are weighted x1.5, so the cloud covers the whole body of
work while the first-author SIDM thread stays visually dominant.

No third-party packages: this machine has no reachable package index, and a
word cloud is not worth a dependency that cannot be installed. The SVG is
written directly.
"""

from __future__ import annotations

import math
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ABSTRACT_DIR = ROOT / "data" / "abstracts"
FULLTEXT_DIR = ROOT / "data" / "fulltext"
OUTPUT = ROOT / "assets" / "img" / "wordcloud.svg"

# --------------------------------------------------------------------------
# Corpus
# --------------------------------------------------------------------------

FIRST_AUTHOR_WEIGHT = 1.5
OTHER_WEIGHT = 1

PAPERS = [
    # (arxiv id, first author?, title)
    ("2604.08647", True, "Bypassed core formation in Milky Way-mass SIDM halos: "
                         "implications for the Local Group past-pericenter scenario"),
    ("2412.14621", True, "Diversity and universality: evolution of dwarf galaxies "
                         "with self-interacting dark matter"),
    ("2310.09910", True, "Till the core collapses: the evolution and properties of "
                         "self-interacting dark matter subhalos"),
    ("2110.00259", True, "Core-collapse, evaporation and tidal effects: the life story "
                         "of a self-interacting dark matter subhalo"),
    ("1808.00357", True, "Effects of neutrino mass and asymmetry on cosmological "
                         "structure formation"),

    ("2605.24174", False, "The sensitivity of substructure lensing to SIDM core-collapse "
                          "model variation"),
    ("2504.13004", False, "Calibrating the SIDM gravothermal catastrophe with N-body "
                          "simulations"),
    ("2402.01604", False, "Convergence tests of self-interacting dark matter simulations"),

    ("2601.23264", False, "MARVELously dark: the gravothermal evolution of dwarf halos "
                          "in velocity-dependent SIDM"),
    ("2403.09597", False, "Tidal evolution of cored and cuspy dark matter halos"),
    ("2305.05067", False, "A quantitative comparison between velocity dependent SIDM "
                          "cross-sections constrained by the gravothermal and isothermal models"),
    ("2205.02957", False, "Gravothermal solutions of SIDM halos: mapping from constant "
                          "to velocity-dependent cross section"),
    ("2206.12425", False, "A semi-analytic study of self-interacting dark-matter haloes "
                          "with baryons"),
    ("1711.05210", False, "Evidence of neutrino enhanced clustering in a complete sample "
                          "of Sloan survey clusters"),
]

# --------------------------------------------------------------------------
# Vocabulary handling
# --------------------------------------------------------------------------

# Multi-word terms are collapsed into single tokens before word splitting.
# Without this the cloud shows "dark", "matter" and "self" separately, which is
# exactly what makes generic astronomy word clouds uninformative. Longest first
# so that "self-interacting dark matter" wins over "dark matter".
PHRASES = [
    "self-interacting dark matter",
    "self interacting dark matter",
    "matter power spectrum",
    "cold dark matter",
    "substructure lensing",
    "structure formation",
    "globular cluster",
    "stellar stream",
    "tidal stripping",
    "tidal evolution",
    "tidal disruption",
    "dwarf galaxy",
    "dwarf spheroidal",
    "core collapse",
    "core formation",
    "cross section",
    "parameter space",
    "initial condition",
    "dark matter",
    "black hole",
    "milky way",
    "local group",
    "power spectrum",
    "star formation",
    "n-body",
    "velocity dispersion",
    "velocity-dependent",
    "mass function",
    "density profile",
    "rotation curve",
]

# Abbreviations folded into the phrase they stand for. Applied to whole words
# before anything else, so "SIDM" and "self-interacting dark matter" count as
# the same term.
ALIASES = {
    "sidm": "self-interacting dark matter",
    "cdm": "cold dark matter",
    "dm": "dark matter",
    "dmo": "dark matter",
    "mw": "milky way",
    "smbh": "black hole",
    "bh": "black hole",
    "ccp": "core collapse",
    "udg": "dwarf galaxy",
    "gc": "globular cluster",
    "haloe": "halo",
    "sub-halo": "subhalo",
}

# Applied to the normalised text before phrases are collapsed, to stop compound
# modifiers from leaking into a phrase token ("milky way-mass" -> "milky way").
PRE_REPLACE = [
    (r"milky way-mass", "milky way"),
    (r"dark matter-only", "dark matter"),
    (r"dark-matter", "dark matter"),
]

# Rendering only; counting is done on the normalised form.
DISPLAY_OVERRIDES = {
    "self interacting dark matter": "self-interacting dark matter",
    "cold dark matter": "cold dark matter",
    "velocity dependent cross section": "velocity-dependent cross section",
    "velocity dependent": "velocity-dependent",
    "cross section": "cross section",
    "n body": "N-body",
    "cmb": "CMB",
    "milky way": "Milky Way",
    "local group": "Local Group",
    "core collapse": "core collapse",
    "nfw": "NFW",
}

# Ordinary English stop words plus the academic filler that dominates naive
# word clouds built from abstracts. Everything in the second block carries no
# information about what the work is about.
STOPWORDS = set("""
a about above after again against all also am an and any are as at
be because been before being below between both but by
can cannot could
did do does doing down during
each either else
few for from further
had has have having he her here hers him his how however
i if in into is it its itself
just
me more most much must my
no nor not
of off on once only or other others our ours out over own
per
same she should so some such
than that the their theirs them then there these they this those through to too
under until up upon us
very via
was we were what when where whether which while who whom why will with within without would
you your yours
""".split()) | set("""
account address adopt allow analyse analyze apply approach argue assume
based become behaviour behavior calculate case cases characterise characterize
compare comparison conclude conclusion consider consistent constrain
demonstrate describe detail determine develop difference different discuss
due effect effects employ enable estimate example examine exhibit expect
explain explore extend find finding finds first focus follow following found
general generate give given good high higher highest identify impact implication
implications imply important include including increase increasing indicate
introduce investigate involve key known large larger largest lead less level
like likely limit low lower main make many measure method methods model models
new note number observe obtain occur one order paper perform possible predict
prediction present previous previously problem produce property propose provide
purpose quantify range rate reach recent regime relate relative report require
respectively result results reveal robust role sample scale scenario section
see set several show shown significant significantly similar simple small
smaller specific standard state strong strongly study suggest summarise
summarize support system systems take term test three total two typical type
understand use used using value various vary well work yield
""".split()) | set("""
till story life marvelously complete evidence especially finite fast drive
may thus size ratio function center track table data note
process equation run since radii region energy group analog star
dashed fraction component orbital massive factor even fit bound ini
lmfp corresponding fitting solid log therefore realization loss baryon blue
dotted black red green gray respectively similar general thf
marvel iii university appendix numerical compared curve radial phase
step measured mean doe usa error
interaction measurement future vir
point end
length
one two three four five six seven eight nine ten
rmax
""".split())

# ---------------------------------------------------------------------------
# Reviewed-out terms (the human/model review layer required by plan §6.4).
#
# Every entry below was looked at individually and rejected for one of two
# reasons, recorded next to it. This list is the final gate: regenerating the
# cloud after adding abstracts will surface new candidates, which should be
# reviewed the same way and either kept or added here.
# ---------------------------------------------------------------------------
REVIEWED_OUT = {
    # -- duplicates of a term that already appears in a better form ----------
    "dark matter",        # carried by "self-interacting dark matter"
    "dark",               # fragment of the above (e.g. "MARVELously dark")
    "dwarf",              # carried by "dwarf galaxy"
    "tidal",              # carried by "tidal evolution"
    "velocity-dependent cross section",  # split into "velocity-dependent" + "cross section"
    "gravothermal catastrophe",          # folded into "gravothermal"
    "gravothermal evolution",            # folded into "gravothermal"
    "catastrophe",        # leftover fragment of "gravothermal catastrophe"

    # -- no standalone meaning: title phrasing or generic modifiers ----------
    "sloan",              # survey name fragment, meaningless in a cloud
    "survey",             # generic wallpaper word (from "Sloan survey clusters")
    "cluster",            # near-duplicate of "clustering", which is the actual term
    "mass",               # generic wallpaper word
    "asymmetry",          # only meaningful inside "neutrino asymmetry"
    "cosmological",       # generic adjective
    "universality",       # title phrasing, vague standalone
    "bypassed",           # title phrasing; "core formation" carries the topic
    "past-pericenter",    # too narrow without its sentence
    "sensitivity", "variation", "calibrating", "convergence",
    "quantitative", "constrained", "mapping", "constant",
    "enhanced", "solution",

    # -- full-text noise: bibliography, figure labels, units, subject tags --
    "arxiv",            # bibliography identifier
    "fig", "figure",    # figure labels
    "astro-ph",         # arXiv subject class
    "gyr", "kpc",       # units
    "cm2",              # cross-section unit
    "line",             # "line of sight", "field line", generic
    "sub",              # fragment ("sub-grid", "sub-structure")

    # -- generic words surfacing in full text ------------------------------
    "time", "half", "radius", "central", "resolution", "inner",
    "isolated", "orbit", "profile", "particle", "initial", "parameter",

    # -- fragments of terms that already appear whole ----------------------
    "core", "collapse", "density", "formation",

    # -- journal-name fragments and LaTeX macros from full-text references --
    "mnra",             # "MNRAS"
    "astron",           # "Astronomical"
    "soc",              # "Society"
    "mon",              # "Monthly"
    "phy",              # "Physics/Physical"
    "pro",              # "Proceedings"
    "sec",              # "Section"
    "ect",              # "etc."
    "rhalf",            # LaTeX r_half macro
    "panel",            # figure panel label

    # -- generic terms surfacing in full text ------------------------------
    "gravitational", "distribution", "potential", "slope", "satellite",
    "velocity",         # carried by "velocity-dependent" / "velocity dispersion"
    "physic",           # "Physical" (journal)
    "core-collapsed",   # duplicate of "core collapse"
    "heat",             # duplicate of "heating"
}

MIN_LENGTH = 3
MAX_WORDS = 40


def normalise(text: str) -> str:
    text = text.lower()
    # unfold typographic ligatures common in extracted PDF text (ﬀ ﬁ ﬂ ﬃ ﬄ …)
    for lig, repl in (("\ufb00", "ff"), ("\ufb01", "fi"), ("\ufb02", "fl"),
                      ("\ufb03", "ffi"), ("\ufb04", "ffl"), ("\ufb05", "ft"),
                      ("\ufb06", "st")):
        text = text.replace(lig, repl)
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    text = re.sub(r"\$[^$]*\$", " ", text)          # inline LaTeX from abstracts
    text = re.sub(r"[^a-z0-9\-'\s]", " ", text)
    text = re.sub(r"-\s+", "", text)                # join words hyphenated across line breaks
    return re.sub(r"\s+", " ", text).strip()


def collapse_phrases(text: str) -> str:
    for phrase in sorted(PHRASES, key=len, reverse=True):
        token = phrase.replace(" ", "_").replace("-", "_")
        # "core collapse", "core-collapse" and "core collapse" written either
        # way all have to fold into the same token.
        variants = {phrase, phrase.replace(" ", "-"), phrase.replace("-", " ")}
        for variant in variants:
            text = re.sub(r"\b" + re.escape(variant) + r"\b", token, text)
    return text


def singularise(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("sses") or word.endswith("ches") or word.endswith("shes"):
        return word[:-2]
    # "analysis", "radius", "previous" are not plurals
    if word.endswith(("ss", "is", "us", "ous")):
        return word
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def singularise_text(text: str) -> str:
    """Fold plurals across the whole string.

    Done before phrases are collapsed so that "core collapses" and "dwarf
    galaxies" reach the phrase table in their singular form; otherwise they
    escape it and show up as loose words next to the phrase they belong to.
    """
    return " ".join(singularise(word) if "-" not in word
                    else "-".join(singularise(p) for p in word.split("-"))
                    for word in text.split())


def tokenise(text: str) -> list[str]:
    text = normalise(text)
    for pattern, replacement in PRE_REPLACE:
        text = re.sub(r"\b" + pattern + r"\b", replacement, text)
    text = singularise_text(text)
    for alias, target in ALIASES.items():
        text = re.sub(r"\b" + re.escape(alias) + r"\b", target, text)
    text = collapse_phrases(text)

    tokens = []
    for raw in text.split():
        if "_" in raw:                               # a collapsed phrase
            if raw.replace("_", " ") not in REVIEWED_OUT:
                tokens.append(raw)
            continue
        word = raw.strip("-'")
        if not word or any(ch.isdigit() for ch in word):
            continue
        if len(word) < MIN_LENGTH or word in STOPWORDS or word in REVIEWED_OUT:
            continue
        tokens.append(word)
    return tokens


def display(token: str) -> str:
    text = token.replace("_", " ")
    return DISPLAY_OVERRIDES.get(text, text)


def build_counts() -> Counter:
    counts: Counter = Counter()
    missing = []
    for arxiv_id, is_first, title in PAPERS:
        weight = FIRST_AUTHOR_WEIGHT if is_first else OTHER_WEIGHT
        text = title
        fulltext_file = FULLTEXT_DIR / f"{arxiv_id}.txt"
        abstract_file = ABSTRACT_DIR / f"{arxiv_id}.txt"
        if fulltext_file.exists():
            text = fulltext_file.read_text(encoding="utf-8")
        elif abstract_file.exists():
            text += " " + abstract_file.read_text(encoding="utf-8")
        else:
            missing.append(arxiv_id)
        for token in tokenise(text):
            counts[token] += weight

    if missing:
        print(f"  abstracts missing for {len(missing)}/{len(PAPERS)} papers "
              f"(title-only for: {', '.join(missing)})")
        print(f"  add them as {ABSTRACT_DIR.relative_to(ROOT)}/<arxiv-id>.txt and rerun")
    return counts


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

CANVAS_W, CANVAS_H = 1000, 500
FONT_MAX, FONT_MIN = 56.0, 14.0
PAD = 4.0

# Deterministic so that reruns produce the same SVG unless the corpus changes.
SEED = 42

# Hue/saturation families, anchored on the site's headingBlue. Lightness is
# assigned by rank within each family so important words still read darkest.
PALETTE = [
    (219, 59),   # headingBlue
    (207, 48),   # steel blue
    (187, 46),   # teal
    (27, 62),    # amber
    (267, 34),   # muted violet
]

# Rough advance widths as a fraction of font size, good enough to keep boxes
# from touching without shipping a font-metrics library.
NARROW = set("ijlt.,'!|-")
WIDE = set("mwMW")


def text_width(text: str, size: float) -> float:
    total = 0.0
    for ch in text:
        if ch in NARROW:
            total += 0.30
        elif ch in WIDE:
            total += 0.86
        elif ch == " ":
            total += 0.28
        elif ch.isupper():
            total += 0.66
        else:
            total += 0.54
    return total * size


def overlaps(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw + PAD < bx or bx + bw + PAD < ax or
                ay + ah + PAD < by or by + bh + PAD < ay)


def layout(entries):
    """Spiral placement, largest word first. All words horizontal."""
    placed = []
    cx, cy = CANVAS_W / 2.0, CANVAS_H / 2.0

    for text, size, count in entries:
        w, h = text_width(text, size), size * 1.02
        spot = None
        t = 0.0
        while t < 400.0:
            r = 2.6 * t
            x = cx + r * math.cos(t) - w / 2.0
            y = cy + r * math.sin(t) * 0.5 - h / 2.0
            box = (x, y, w, h)
            if 0 <= x and x + w <= CANVAS_W and 0 <= y and y + h <= CANVAS_H:
                if not any(overlaps(box, p[0]) for p in placed):
                    spot = box
                    break
            t += 0.10
        if spot is not None:
            placed.append((spot, text, size, count))
    return placed


def colour(rank: int, total: int, rng: random.Random) -> str:
    """Multi-hue palette; lightness still tracks rank so big words read darkest."""
    frac = rank / max(total - 1, 1)
    if rank == 0:
        hue, sat = PALETTE[0]           # the headline term stays on brand
    else:
        hue, sat = rng.choice(PALETTE)
    light = 26 + 34 * frac
    return f"hsl({hue:.0f}, {sat:.0f}%, {light:.0f}%)"


def render(placed) -> str:
    if not placed:
        raise SystemExit("nothing placed")

    rng = random.Random(SEED + 1)
    xs0 = min(b[0][0] for b in placed)
    ys0 = min(b[0][1] for b in placed)
    xs1 = max(b[0][0] + b[0][2] for b in placed)
    ys1 = max(b[0][1] + b[0][3] for b in placed)
    m = 10.0
    vb = f"{xs0 - m:.1f} {ys0 - m:.1f} {xs1 - xs0 + 2 * m:.1f} {ys1 - ys0 + 2 * m:.1f}"

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" '
        f'aria-label="Word cloud of the most frequent terms across all publications">',
        '  <title>Most frequent terms across all publications</title>',
        '  <g font-family="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" '
        'font-weight="600">',
    ]
    for rank, (box, text, size, count) in enumerate(placed):
        x, y, _w, h = box
        fill = colour(rank, len(placed), rng)
        safe = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        baseline = y + h * 0.80
        lines.append(
            f'    <text x="{x:.1f}" y="{baseline:.1f}" font-size="{size:.1f}" '
            f'fill="{fill}">{safe}</text>'
        )
    lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    print("building word cloud")
    counts = build_counts()
    top = counts.most_common(MAX_WORDS)
    if not top:
        raise SystemExit("empty corpus")

    hi = top[0][1]
    lo = top[-1][1]
    entries = []
    for token, count in top:
        # sqrt scaling keeps the largest word from swallowing the canvas
        frac = 0.0 if hi == lo else (math.sqrt(count) - math.sqrt(lo)) / (math.sqrt(hi) - math.sqrt(lo))
        text = display(token)
        size = FONT_MIN + (FONT_MAX - FONT_MIN) * frac
        # Long phrases such as "self-interacting dark matter" would otherwise be
        # wide enough to leave no room for anything else on the same row.
        limit = 0.62 * CANVAS_W
        if text_width(text, size) > limit:
            size = size * limit / text_width(text, size)
        entries.append((text, size, count))
    # keep placement priority by rendered size, since the width cap above can
    # reorder a couple of entries relative to their raw counts
    entries.sort(key=lambda e: e[1], reverse=True)

    placed = layout(entries)
    dropped = len(entries) - len(placed)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(placed), encoding="utf-8")

    print(f"  {len(placed)} words placed" + (f", {dropped} dropped (no room)" if dropped else ""))
    print(f"  wrote {OUTPUT.relative_to(ROOT)}")
    print("\n  final word list (already filtered through REVIEWED_OUT):")
    for token, count in top:
        print(f"    {count:5.1f}  {display(token)}")


if __name__ == "__main__":
    main()
