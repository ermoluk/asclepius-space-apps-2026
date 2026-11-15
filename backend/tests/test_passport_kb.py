"""Guard: field/modifier IDs in PREFLIGHT_TIMELINE.feeds must exist in the passport KB."""
import re
from pathlib import Path

from app.passport import PREFLIGHT_TIMELINE

KB = Path(__file__).resolve().parents[2] / "knowledge-base" / "01-physiological-passport.md"
_ID = re.compile(r"^(?:[A-M]\d{1,2}|P-\d{2})(?=\s|$)")


def _kb_ids():
    ids = set()
    for line in KB.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*((?:[A-M]\d{1,2})|(?:P-\d{2}))\s*\|", line)
        if m:
            ids.add(m.group(1))
    return ids


def test_feeds_ids_exist_in_kb():
    kb = _kb_ids()
    assert {"A7", "D10", "P-23", "K3", "L5"} <= kb
    used = [(s["id"], f.split()[0]) for s in PREFLIGHT_TIMELINE for f in s["feeds"] if _ID.match(f)]
    assert used
    missing = [(sid, i) for sid, i in used if i not in kb]
    assert not missing, missing


def test_feeds_ids_match_kb_timeline_table():
    text = KB.read_text(encoding="utf-8")
    for s in PREFLIGHT_TIMELINE:
        for f in s["feeds"]:
            if _ID.match(f):
                assert f.split()[0] in text
