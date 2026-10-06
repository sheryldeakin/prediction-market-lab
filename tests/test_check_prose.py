"""The prose gate: extraction, one fixture per family, exemptions, exit code."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_prose as cp


def families(text):
    return {fam for _, fam, _ in cp.check_text(text)}


# ---- prose extraction ----

def test_extraction_drops_non_prose_and_keeps_paragraphs_and_bullets():
    text = "\n".join([
        "Kept paragraph line.",                       # 1
        "<!-- table:headline:start -->",              # 2
        "Moreover this is inside a splice.",          # 3
        "<!-- table:headline:end -->",                # 4
        "<!-- forward:start -->",                     # 5
        "Moreover this is inside a forward block.",   # 6
        "<!-- forward:end -->",                       # 7
        "<!-- a comment with Moreover in it -->",     # 8
        "<!-- multi-line",                            # 9
        "Moreover still a comment -->",               # 10
        "| Moreover | a table line |",                 # 11
        "```",                                        # 12
        "Moreover inside a fence.",                   # 13
        "```",                                        # 14
        "![Moreover](image.png)",                     # 15
        "Text with `Moreover` as inline code.",       # 16
        "- A kept bullet.",                           # 17
    ])
    kept = [(n, t) for n, t in cp.prose_lines(text) if t.strip()]
    assert [n for n, _ in kept] == [1, 16, 17]
    assert "Moreover" not in " ".join(t for _, t in kept)
    assert cp.check_text(text) == []


# ---- one fixture per family ----

BLOCKING_FIXTURES = {
    "A-emdash": "The model — a forest — fits.",
    "B-marker": "The run ended. Moreover the next one started.",
    "C-pivot": "This is not just a model but a test.",
    "E-interjection": "The rows, together, agree.",
    "G-metaphor": "The result speaks to the fit.",
    "J-intensifier": "The gap is very small.",
    "M-padding": "We sort the rows in order to compare.",
    "U-vocab": "We delve into the rows.",
    "T-stilted": "The result ought to hold.",
    "V-overclaim": "The run proves the gap.",
}
ADVISORY_FIXTURES = {
    "X-long": " ".join(["word"] * 40) + ".",
    "R-impersonal": "One might expect a gap.",
    "K-opener": "- **A lead that is clearly longer than six words**: then the text.",
    "O-hedge": "The gap appears to suggest a drift.",
}


@pytest.mark.parametrize("family,line", sorted({**BLOCKING_FIXTURES, **ADVISORY_FIXTURES}.items()))
def test_each_fixture_hits_exactly_its_family(family, line):
    assert families(line) == {family}


def test_every_family_has_a_fixture():
    assert set(BLOCKING_FIXTURES) | set(ADVISORY_FIXTURES) == set(cp.ALL_FAMILIES)


def test_two_hyphen_dash_and_other_pivots_and_start_positions():
    assert families("The gap -- a small one -- stays.") == {"A-emdash"}
    assert families("Not only the open but also the close moved.") == {"C-pivot"}
    assert families("The row is not a fluke. It is a pattern.") == {"C-pivot"}
    assert families("It stays flat, full stop.") == {"C-pivot"}
    # sentence start: after a colon, after a bullet marker, and at a line start
    assert families("Result: Thus the gap closed.") == {"B-marker"}
    assert families("- Hence the gap closed.") == {"B-marker"}
    # mid-sentence is not a sentence start, and the match is case-sensitive
    assert families("The gap closed and thus stayed shut.") == set()


# ---- exemptions ----

@pytest.mark.parametrize("line", [
    "Every window is scored.",                    # very inside every
    "The room was quiet.",                        # quite inside quiet
    "See the confirmation row.",                  # confirm inside confirmation
    "The gain is significantly, p = 0.03, above zero.",
    "The gain is significant at 5%.",
    "The robust row is the strict one.",
    "The resamples yield the interval.",
    "In the test, the test confirms the shape.",
    "We demonstrate the interface in the page.",
    "The coverage guarantee holds at every target.",     # conformal prediction's defined property
    "A threshold that guarantees a coverage rate.",
    "Reclaims, retests, confirmed breaks and the confirmed breakout.",   # library phrase names
])
def test_technical_register_exemptions_do_not_fire(line):
    assert cp.check_text(line) == []


def test_significantly_without_a_number_still_fires():
    assert families("The gap is significantly larger.") == set()  # not a J/B row mid-sentence
    assert families("Significantly, the gap closed.") == {"B-marker"}


# ---- exit code ----

def test_exit_code_is_one_with_a_blocking_hit_and_zero_with_only_advisory(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_text("The model — a forest — fits.\n", encoding="utf-8")
    assert cp.main([str(bad), "--summary"]) == 1
    soft = tmp_path / "soft.md"
    soft.write_text("One might expect a gap.\n", encoding="utf-8")
    assert cp.main([str(soft), "--summary"]) == 0
    out = capsys.readouterr().out
    assert "advisory" in out and "exit code: 0" in out


def test_json_writes_counts(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("The run proves the gap.\n", encoding="utf-8")
    out = tmp_path / "counts.json"
    cp.main([str(f), "--summary", "--json", str(out)])
    import json
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["counts"]["a.md"] == {"V-overclaim": 1}
    assert data["blocking"] == 1 and data["exit_code"] == 1


def test_gate_can_fail_the_em_dash_row_must_exist():
    # Removing the A-emdash row empties this set and fails the test.
    assert "A-emdash" in families("A dash — here.")
    assert cp.is_blocking("A-emdash")
