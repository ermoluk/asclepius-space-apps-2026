from pathlib import Path

from app.kb import load_kb


def test_kb_counts():
    kb = load_kb()
    assert len(kb.conditions) == 115
    assert len(kb.actions) == 102
    assert "TB004" in kb.references
    assert kb.conditions["C098"]["system"] == "EYE"


def test_condition_shape():
    kb = load_kb()
    c = kb.conditions["C001"]
    assert set(c) == {"id", "name", "system", "type", "max_level", "features", "confirm", "refs"}
    assert c["max_level"] == "RED"
    assert c["refs"] == ["IMM-MYERS", "ATLS"]
    assert kb.conditions["X01"]["type"] == "X"


def test_actions_and_references_shape():
    kb = load_kb()
    a = kb.actions["A-GEN-02"]
    assert a["text"] == "Inform your Crew Medical Officer now."
    assert a["who"]
    assert kb.references["NEWS2"]["url"].startswith("https://")
    assert kb.references["GCS"]["url"] is None
    assert "*" not in kb.references["BARGER2014"]["title"]


def test_default_path_independent_of_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(load_kb().conditions) == 115


def test_rules_default_empty_and_custom_path(tmp_path):
    kb = load_kb()
    assert isinstance(kb.rules, list)
    for n in ("conditions", "actions", "references"):
        (tmp_path / f"{n}.yaml").write_text("{}\n")
    (tmp_path / "rules.yaml").write_text("- id: R1\n")
    assert load_kb(tmp_path).rules == [{"id": "R1"}]
