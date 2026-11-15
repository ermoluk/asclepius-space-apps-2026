"""Load the compiled knowledge base (backend/knowledge/*.yaml)."""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "knowledge"


@dataclass
class KB:
    conditions: dict
    actions: dict
    references: dict
    rules: list = field(default_factory=list)


def _load(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_kb(path: Path | str | None = None) -> KB:
    base = Path(path) if path is not None else DEFAULT_PATH
    rules_file = base / "rules.yaml"
    return KB(
        conditions=_load(base / "conditions.yaml") or {},
        actions=_load(base / "actions.yaml") or {},
        references=_load(base / "references.yaml") or {},
        rules=(_load(rules_file) or []) if rules_file.exists() else [],
    )
