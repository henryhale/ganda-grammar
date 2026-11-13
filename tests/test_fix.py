import json

import pytest

from ganda_grammar.cli import main
from ganda_grammar.fix import fix


@pytest.fixture
def corpus(tmp_path):
    src = tmp_path / "in"
    (src / "sub").mkdir(parents=True)
    (src / "a.txt").write_bytes("Na abantu bagenda.\r\nThe dog sleeps.\nebitabo kyange\n".encode())
    rows = [{"id": 1, "text": "na abantu", "lug": "mukibuga", "n": 2.5}, {"id": 2, "text": "Abantu bangi."}]
    (src / "sub" / "b.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows) + "not json {\n[1, 2]\n", encoding="utf-8")
    (src / "notes.html").write_text("na abantu")
    return src


@pytest.mark.parametrize("workers", [1, 2])
def test_fix_writes_corrected_copies(corpus, tmp_path, workers):
    out = tmp_path / "out"
    r = fix([corpus], out, ["text", "lug"], workers=workers, log=tmp_path / "log.jsonl")

    assert (out / "a.txt").read_bytes() == "N'abantu bagenda.\r\nThe dog sleeps.\nebitabo byange\n".encode()
    lines = (out / "sub" / "b.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == {"id": 1, "text": "n'abantu", "lug": "mu kibuga", "n": 2.5}
    assert lines[1:] == ['{"id": 2, "text": "Abantu bangi."}', "not json {", "[1, 2]"]  # untouched, byte for byte
    assert not (out / "notes.html").exists()
    assert (corpus / "a.txt").read_bytes().startswith(b"Na abantu")  # input unchanged

    assert (r.seen, r.changed) == (7, 3)
    assert r.counts == {"ELISION_NA": 2, "AGREE_POSS": 1, "SPLIT_LOC": 1}
    log = [json.loads(line) for line in (tmp_path / "log.jsonl").open(encoding="utf-8")]
    assert len(log) == 4
    for row in log:  # each logged edit replays the change
        text = row["original"]
        for e in reversed(row["edits"]):
            assert text[e["start"]:e["end"]] == e["before"]
            text = text[:e["start"]] + e["after"] + text[e["end"]:]
        assert text == row["corrected"]


def test_fix_refuses_to_overwrite_its_input(corpus):
    with pytest.raises(ValueError, match="overwrite"):
        fix([corpus / "a.txt"], corpus, workers=1)


def test_cli_correct(capsys):
    main(["correct", "na abantu"])
    assert capsys.readouterr().out == "n'abantu\n"
    main(["correct", "--json", "na bo"])
    assert json.loads(capsys.readouterr().out)["edits"][0]["rule"] == "JOIN_NA_PRONOUN"


def test_cli_fix(corpus, tmp_path, capsys):
    main(["fix", str(corpus), "-o", str(tmp_path / "out"), "--workers", "1"])
    assert "ELISION_NA\t2" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["fix", "-o", str(tmp_path / "out")])
