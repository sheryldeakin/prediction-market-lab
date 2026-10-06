"""The numbers the docs repeat by hand agree with what the docs contain."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_readme_study_count_matches_the_report():
    report = (ROOT / "docs" / "btc_15m.md").read_text(encoding="utf-8")
    numbered = {int(m) for m in re.findall(r"^\*\*(\d+)\. ", report, flags=re.M)}
    assert numbered == set(range(1, max(numbered) + 1)), "study numbering has a gap"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    counts = {int(m) for m in re.findall(r"(\d+) studies", readme)}
    assert counts == {max(numbered)}, f"README says {counts}, the report has {max(numbered)} studies"


def test_every_table_marker_has_a_generated_source():
    for doc in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        text = doc.read_text(encoding="utf-8")
        for name in re.findall(r"<!-- table:([a-z_0-9]+):start -->", text):
            assert (ROOT / "results" / "btc_15m" / f"{name}.md").exists(), f"{doc.name}: no results/btc_15m/{name}.md"
            assert f"<!-- table:{name}:end -->" in text, f"{doc.name}: {name} has no end marker"


# Blocking since the docs prose pass of 2026-10-06; a retired phrasing goes into scripts/check_prose.py the day it is retired.
def test_docs_prose_has_no_blocking_language_hits():
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_prose
    results = check_prose.check_files(check_prose.default_files())
    blocking = [f"{name}:{n}: {fam}" for name, hits in results.items()
                for n, fam, _ in hits if check_prose.is_blocking(fam)]
    assert not blocking, f"{len(blocking)} blocking hits, first: {blocking[:5]}"
