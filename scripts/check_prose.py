"""Language gate for the docs: prose only, blocking and advisory rows.

Usage: python scripts/check_prose.py [files...] [--summary] [--json PATH]
Default files: README.md and docs/*.md. Exit 1 when any blocking row hits.

Only prose is checked. Dropped before any row runs: generated table splices
(<!-- table:NAME:start --> ... <!-- table:NAME:end -->), forward-log splices
(<!-- forward:start --> ... <!-- forward:end -->), every other HTML comment,
fenced code blocks, pipe-table lines, image lines and inline code spans.

Add a row whenever a phrasing is retired; never delete rows.
"""
import argparse
import bisect
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Technical-register exemptions. The matched span is blanked before any row
# runs, so a word that is precise in this repo cannot fire. Kept short on
# purpose; each entry says why it is precise here.
EXEMPT = [
    # "robust" is a metric name here (the robust row of the cell tables).
    r"\brobust\b",
    # "yield(s)" is statistics here (the resamples yield the interval).
    r"\byields?\b",
    # a tested claim: "significantly, p = 0.03", "significant at 5%".
    r"\bsignificant(?:ly)?\b(?=.{0,12}?(?:\d|%|\bp\b))",
    # a test confirming a result is a statement about code, not a claim.
    r"\btests? confirms?\b",
    # the one sanctioned use of demonstrate.
    r"\bdemonstrate the interface\b",
]
# Not listed because word boundaries already protect them: "confirmation"
# (confirm), "every" (very), "quiet" (quite).

MARKERS = [
    "In fact", "Indeed", "Of course", "Naturally", "Clearly", "Obviously",
    "Crucially", "Notably", "Importantly", "Critically", "Strikingly",
    "Tellingly", "Significantly", "Surprisingly", "Interestingly",
    "Remarkably", "Moreover", "Furthermore", "Additionally", "Hence", "Thus",
    "Therefore", "By contrast", "In contrast", "Conversely", "Similarly",
    "Likewise", "In essence", "In summary", "In conclusion", "In short",
    "That said", "To be clear", "In other words", "Put simply",
    "Put differently", "It turns out", "The fact is",
]
# Sentence start: a line start (after a bullet or quote marker), or after
# ". ", ": ", "! ", "? ", or a bold lead's closing "**" plus space.
_START = r"(?:^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s*)?(?:\*\*)?|(?<=[.:!?] )|(?<=[.:!?]\*\* ))"


def _words(items, flags=re.I):
    return re.compile(r"\b(?:" + "|".join(items) + r")\b", flags)


def _phrases(items):
    return re.compile("|".join(re.escape(i) for i in items), re.I)


# family -> (blocking, [compiled patterns])
FAMILIES = {
    "A-emdash": (True, [re.compile("—"), re.compile(r"(?<=\s)--(?=\s)")]),
    "B-marker": (True, [re.compile(_START + "(?:" + "|".join(re.escape(m) for m in MARKERS) + r")\b")]),
    "C-pivot": (True, [
        re.compile(r"not just \w+.{0,40}(?:but|it is|it's)", re.I),
        re.compile(r"not only .{0,60} but also", re.I),
        re.compile(r"is not (?:a |an )?\w+[.;] (?:It|They) (?:is|are)\b"),
        re.compile(r", full stop\b", re.I),
        re.compile(r", period\.", re.I),
    ]),
    "E-interjection": (True, [_phrases([
        ", together,", ", collectively,", ", in turn,", ", in tandem,",
        ", taken together,", ", on balance,", ", by and large,",
        ", for the most part,", ", broadly speaking,", ", which is to say,",
        ", that is to say,",
    ])]),
    "G-metaphor": (True, [_words([
        "lies at the heart of", "comes down to", "the crux of", "speaks to",
        "cuts against", "comports with", "stands in tension with",
        "sits at the intersection of", "sheds light on", "casts light on",
        "through the lens", "tells a story", "the story is", "a clear story",
        "what emerges is", "what we see is", "the bedrock", "the cornerstone",
        "unlocking", "uncovering", "paves the way", "bridges the gap",
        "a crucial step", "pivotal",
    ])]),
    "J-intensifier": (True, [_words([
        "actually", "genuinely", "essentially", "fundamentally", "ultimately",
        "inherently", "remarkably", "strikingly", "profoundly", "deeply",
        "very", "quite", "compelling", "elegant", "sophisticated",
    ])]),
    "M-padding": (True, [_words([
        "it is important to note", "it is worth noting", "it bears mentioning",
        "it should be noted", "in order to", "due to the fact that",
        "in spite of the fact that", "with respect to", "with regard to",
        "in the context of", "by virtue of", "for the purposes of",
        "there exists", "it can be shown that",
    ])]),
    "U-vocab": (True, [_words([
        "delve", "delves", "delving", "underscores?", "intricate", "tapestry",
        "testament", "landscape", "realm", "showcase", "foster", "leverage",
        "seamless(?:ly)?", "serves as", "groundbreaking", "vibrant",
        "highlighting the importance",
    ])]),
    "T-stilted": (True, [_words([
        "borne out", "bear out", "obtains", "ought to", "stands to reason",
        "to that end", "to this end", "in any event", "at any rate",
        "in keeping with", "in accordance with", "owing to", "by way of",
        "insofar as", "inasmuch as", "in so doing", "in doing so", "whereupon",
        "wherein", "whereby", "thereby", "therein",
    ])]),
    "V-overclaim": (True, [_words([
        r"prove[sd]?", r"demonstrat(?:e|es|ed)", r"confirm(?:s|ed)?",
        r"guarantees?", "universally", "in all cases",
    ])]),
    "R-impersonal": (False, [_phrases([
        "one might", "one would", "one could", "one expects", "the reader might",
    ])]),
    "O-hedge": (False, [_phrases([
        "appears to suggest", "seems to suggest", "might possibly",
        "may potentially", "could possibly",
    ])]),
}
# X-long and K-opener are structural, computed from paragraphs below.
ADVISORY_STRUCTURAL = {"X-long": 35, "K-opener": 6}
ALL_FAMILIES = [*FAMILIES, *ADVISORY_STRUCTURAL]
BLOCKING = {f for f, (b, _) in FAMILIES.items() if b}

_EXEMPT_RES = [re.compile(p, re.I) for p in EXEMPT]
_SPLICE_START = re.compile(r"<!--\s*(table:[\w]+|forward):start\s*-->")
_SPLICE_END = re.compile(r"<!--\s*(table:[\w]+|forward):end\s*-->")
_COMMENT = re.compile(r"<!--.*?-->")
_INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
_BULLET = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")


def prose_lines(text):
    """Return [(lineno, cleaned_line)] for the prose in `text`, 1-based."""
    out = []
    splice = None      # name of the splice block being skipped
    in_comment = False
    in_fence = False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw
        if splice:
            m = _SPLICE_END.search(line)
            if m and m.group(1) == splice:
                splice = None
            continue
        m = _SPLICE_START.search(line)
        if m:
            if not _SPLICE_END.search(line[m.end():]):
                splice = m.group(1)
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
                line = line.split("-->", 1)[1]
            else:
                continue
        line = _COMMENT.sub("", line)
        if "<!--" in line:
            in_comment = True
            line = line.split("<!--", 1)[0]
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith("|") or stripped.startswith("!["):
            out.append((n, ""))
            continue
        line = _INLINE_CODE.sub(" ", line)
        out.append((n, line))
    return out


def _mask(line):
    for rx in _EXEMPT_RES:
        line = rx.sub(lambda m: " " * len(m.group(0)), line)
    return line


def _context(line, start, end):
    mid = (start + end) // 2
    lo = max(0, min(mid - 40, len(line) - 80))
    return line[lo:lo + 80].strip()


def _paragraphs(lines):
    """Group cleaned lines into paragraphs: [(first_line_no, [(no, text)])].
    A blank line, a heading, a bullet start or a gap in line numbers ends one."""
    paras, cur, prev = [], [], None
    for n, t in lines:
        blank = not t.strip()
        head = t.lstrip().startswith("#")
        new = blank or head or _BULLET.match(t) or (prev is not None and n != prev + 1)
        if new and cur:
            paras.append(cur)
            cur = []
        if not blank and not head:
            cur.append((n, t))
        prev = n
    if cur:
        paras.append(cur)
    return paras


def _structural(paras):
    hits = []
    for para in paras:
        # K-opener: a lead before a colon longer than six words.
        first_no, first = para[0]
        s = _BULLET.sub("", first, count=1).strip()
        lead = None
        if s.startswith("**"):
            close = s.find("**", 2)
            if close > 0:
                inner = s[2:close]
                rest = s[close + 2:]
                if inner.endswith(":") or rest.startswith(":"):
                    lead = inner.rstrip(":")
        else:
            m = re.match(r"([^:.!?]+):\s", s)
            if m:
                lead = m.group(1)
        if lead is not None and len(lead.split()) > ADVISORY_STRUCTURAL["K-opener"]:
            hits.append((first_no, "K-opener", s[:80]))
        # X-long: sentences over 35 words, line mapped through offsets.
        joined, starts = "", []
        for no, t in para:
            starts.append((len(joined), no))
            joined += t.strip() + " "
        offs = [o for o, _ in starts]
        pos = 0
        for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(\[*])", joined):
            idx = joined.find(sent, pos)
            pos = idx + len(sent)
            if len(sent.split()) > ADVISORY_STRUCTURAL["X-long"]:
                no = starts[bisect.bisect_right(offs, idx) - 1][1]
                hits.append((no, "X-long", f"{len(sent.split())} words: {sent[:60]}"))
    return hits


def check_text(text):
    """Return [(lineno, family, context)] sorted by line, for all families."""
    lines = prose_lines(text)
    hits = []
    for n, line in lines:
        if not line.strip():
            continue
        masked = _mask(line)
        for family, (_, pats) in FAMILIES.items():
            for rx in pats:
                for m in rx.finditer(masked):
                    hits.append((n, family, _context(line, m.start(), m.end())))
    hits.extend(_structural(_paragraphs(lines)))
    hits.sort(key=lambda h: (h[0], h[1]))
    return hits


def is_blocking(family):
    return family in BLOCKING


def default_files():
    return [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]


def check_files(paths):
    """{path_name: [(lineno, family, context)]}"""
    return {Path(p).name: check_text(Path(p).read_text(encoding="utf-8")) for p in paths}


def counts(results):
    """{file: {family: n}}, only families that hit."""
    return {f: dict(Counter(h[1] for h in hits)) for f, hits in results.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--summary", action="store_true", help="print only the table")
    ap.add_argument("--json", metavar="PATH", help="write the counts as JSON")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(errors="replace")
    paths = [Path(f) for f in args.files] or default_files()
    missing = [p for p in paths if not p.exists()]
    if missing:
        print("no such file:", ", ".join(map(str, missing)), file=sys.stderr)
        return 2
    results = check_files(paths)
    if not args.summary:
        for f, hits in results.items():
            for n, fam, ctx in hits:
                print(f"{f}:{n}: {fam}: {ctx}")
        print()
    table = counts(results)
    print(f"{'file':<20} {'family':<16} {'kind':<9} {'count':>5}")
    totals = Counter()
    for f in results:
        for fam in ALL_FAMILIES:
            n = table[f].get(fam, 0)
            if n:
                kind = "blocking" if is_blocking(fam) else "advisory"
                print(f"{f:<20} {fam:<16} {kind:<9} {n:>5}")
                totals[kind] += n
    print(f"{'total':<20} {'':<16} {'blocking':<9} {totals['blocking']:>5}")
    print(f"{'total':<20} {'':<16} {'advisory':<9} {totals['advisory']:>5}")
    code = 1 if totals["blocking"] else 0
    if args.json:
        payload = {"counts": table, "blocking": totals["blocking"],
                   "advisory": totals["advisory"], "exit_code": code}
        Path(args.json).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"exit code: {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
