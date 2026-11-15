"""Compile ../knowledge-base/*.md pipe tables into knowledge/*.yaml."""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "knowledge-base"
OUT = ROOT / "knowledge"


def table_rows(text: str):
    """Yield (header_cells, row_cells) for every data row of every pipe table."""
    header = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
        elif all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        else:
            yield header, cells


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[`*]", "", s)).strip()


def refs(s: str):
    return re.findall(r"\[([^\]]+)\]", s)


def conditions():
    text = (SRC / "04-conditions.md").read_text(encoding="utf-8")
    out = {}
    for h, c in table_rows(text):
        if h[0] != "ID" or not re.fullmatch(r"[CX]\d+", c[0]):
            continue
        row = dict(zip(h, c))
        out[c[0]] = {
            "id": c[0],
            "name": clean(row["Condition"]),
            "system": clean(row["Sys"]),
            "type": clean(row.get("Type", "X")),
            "max_level": clean(row["Max"]).upper(),
            "features": clean(row["What the app looks for"]),
            "confirm": clean(row["Confirm with"]),
            "refs": refs(row["Refs"]),
        }
    return out


def actions():
    text = (SRC / "07-actions.md").read_text(encoding="utf-8")
    out = {}
    for h, c in table_rows(text):
        if h[0] != "ID" or not c[0].startswith("A-"):
            continue
        out[c[0]] = {"id": c[0], "text": c[1], "who": c[2]}
    return out


def references():
    text = (SRC / "08-references.md").read_text(encoding="utf-8")
    out = {}
    for h, c in table_rows(text):
        if h[0] != "Key":
            continue
        m = re.search(r"https?://[^\s|)>]+", c[2]) or re.search(r"https?://[^\s|)>]+", " ".join(c))
        out[c[0]] = {
            "key": c[0],
            "title": clean(c[1].replace("✔", "")),
            "url": m.group(0) if m else None,
        }
    return out


def main():
    OUT.mkdir(exist_ok=True)
    for name, fn in (("conditions", conditions), ("actions", actions), ("references", references)):
        data = fn()
        (OUT / f"{name}.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000),
            encoding="utf-8",
        )
        print(f"{name}: {len(data)}")


if __name__ == "__main__":
    sys.exit(main())
